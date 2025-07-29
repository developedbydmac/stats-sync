import pytest
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.services.sports_data_service import SportsDataService
from src.services.parlay_service import ParlayService
from src.utils.prop_analyzer import PropAnalyzer
from src.models.parlay import SportType, TierType, PropType

class TestPropIngestion:
    """Test prop data ingestion and processing"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.sports_service = SportsDataService()
        self.parlay_service = ParlayService()
        self.prop_analyzer = PropAnalyzer("../data/historical_props.csv")
    
    @pytest.mark.asyncio
    async def test_fetch_nfl_props(self):
        """Test fetching NFL player props"""
        props = await self.sports_service.fetch_player_props(SportType.NFL)
        
        assert len(props) > 0, "Should return props data"
        
        # Validate prop structure
        prop = props[0]
        required_fields = ["player_name", "team", "opponent", "prop_type", "line", "over_odds", "under_odds"]
        for field in required_fields:
            assert field in prop, f"Prop should contain {field}"
        
        print(f"✅ Successfully fetched {len(props)} NFL props")
    
    @pytest.mark.asyncio
    async def test_fetch_mlb_props(self):
        """Test fetching MLB player props"""
        props = await self.sports_service.fetch_player_props(SportType.MLB)
        
        assert len(props) > 0, "Should return props data"
        
        # Validate prop structure
        prop = props[0]
        required_fields = ["player_name", "team", "opponent", "prop_type", "line", "over_odds", "under_odds"]
        for field in required_fields:
            assert field in prop, f"Prop should contain {field}"
        
        print(f"✅ Successfully fetched {len(props)} MLB props")
    
    def test_historical_data_loading(self):
        """Test loading and parsing historical prop data"""
        assert self.prop_analyzer.historical_data is not None, "Historical data should be loaded"
        assert len(self.prop_analyzer.historical_data) > 0, "Should have historical records"
        
        # Test required columns
        required_columns = ["player_name", "date", "prop_type", "line", "actual_result", "hit", "odds", "sport"]
        for col in required_columns:
            assert col in self.prop_analyzer.historical_data.columns, f"Should have {col} column"
        
        print(f"✅ Successfully loaded {len(self.prop_analyzer.historical_data)} historical records")
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation for players"""
        # Test with known player
        hit_rate = self.prop_analyzer.get_player_hit_rate("Patrick Mahomes", PropType.PASSING_YARDS)
        
        assert 0 <= hit_rate <= 1, "Hit rate should be between 0 and 1"
        print(f"✅ Patrick Mahomes passing yards hit rate: {hit_rate:.2%}")
        
        # Test with unknown player (should fall back to prop type average)
        unknown_hit_rate = self.prop_analyzer.get_player_hit_rate("Unknown Player", PropType.PASSING_YARDS)
        assert 0 <= unknown_hit_rate <= 1, "Should return valid hit rate for unknown player"
        print(f"✅ Unknown player fallback hit rate: {unknown_hit_rate:.2%}")
    
    def test_confidence_scoring(self):
        """Test confidence score calculation"""
        confidence = self.prop_analyzer.calculate_confidence_score(
            "Patrick Mahomes", 
            PropType.PASSING_YARDS, 
            275.5
        )
        
        assert 0 <= confidence <= 100, "Confidence should be between 0 and 100"
        print(f"✅ Patrick Mahomes confidence score: {confidence:.1f}%")
        
        # Test multiple players
        test_players = [
            ("Josh Allen", PropType.PASSING_YARDS),
            ("Travis Kelce", PropType.RECEIVING_YARDS),
            ("Derrick Henry", PropType.RUSHING_YARDS),
            ("Aaron Judge", PropType.HOME_RUNS),
            ("Gerrit Cole", PropType.STRIKEOUTS)
        ]
        
        for player, prop_type in test_players:
            confidence = self.prop_analyzer.calculate_confidence_score(player, prop_type, 100.0)
            assert 0 <= confidence <= 100, f"Invalid confidence for {player}"
            print(f"✅ {player} {prop_type.value} confidence: {confidence:.1f}%")

class TestParlayBuilder:
    """Test parlay generation and building logic"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parlay_service = ParlayService()
    
    @pytest.mark.asyncio
    async def test_generate_free_tier_parlays(self):
        """Test generating Free tier parlays"""
        parlays = await self.parlay_service.get_parlays(SportType.NFL, TierType.FREE)
        
        assert len(parlays) > 0, "Should generate Free tier parlays"
        
        for parlay_response in parlays:
            parlay = parlay_response.parlay
            assert parlay.tier == TierType.FREE, "Should be Free tier"
            assert parlay.overall_confidence >= 70, "Free tier should have 70%+ confidence"
            assert 5 <= len(parlay.legs) <= 6, "Free tier should have 5-6 legs"
            
        print(f"✅ Generated {len(parlays)} Free tier parlays")
    
    @pytest.mark.asyncio
    async def test_generate_premium_tier_parlays(self):
        """Test generating Premium tier parlays"""
        parlays = await self.parlay_service.get_parlays(SportType.NFL, TierType.PREMIUM)
        
        assert len(parlays) > 0, "Should generate Premium tier parlays"
        
        for parlay_response in parlays:
            parlay = parlay_response.parlay
            assert parlay.tier == TierType.PREMIUM, "Should be Premium tier"
            assert parlay.overall_confidence >= 80, "Premium tier should have 80%+ confidence"
            assert 5 <= len(parlay.legs) <= 7, "Premium tier should have 5-7 legs"
            
        print(f"✅ Generated {len(parlays)} Premium tier parlays")
    
    @pytest.mark.asyncio
    async def test_generate_goat_tier_parlays(self):
        """Test generating GOAT tier parlays"""
        parlays = await self.parlay_service.get_parlays(SportType.NFL, TierType.GOAT)
        
        # GOAT tier might not always have parlays due to strict requirements
        if len(parlays) > 0:
            for parlay_response in parlays:
                parlay = parlay_response.parlay
                assert parlay.tier == TierType.GOAT, "Should be GOAT tier"
                assert parlay.overall_confidence >= 95, "GOAT tier should have 95%+ confidence"
                assert 5 <= len(parlay.legs) <= 8, "GOAT tier should have 5-8 legs"
            
            print(f"✅ Generated {len(parlays)} GOAT tier parlays")
        else:
            print("⚠️ No GOAT tier parlays generated (strict requirements)")
    
    @pytest.mark.asyncio
    async def test_parlay_leg_validation(self):
        """Test individual parlay leg validation"""
        parlays = await self.parlay_service.get_parlays(SportType.NFL)
        
        assert len(parlays) > 0, "Should have parlays to validate"
        
        for parlay_response in parlays:
            parlay = parlay_response.parlay
            
            # Test no duplicate players
            player_names = [leg.player_prop.player_name for leg in parlay.legs]
            assert len(player_names) == len(set(player_names)), "No duplicate players in parlay"
            
            # Test team distribution (max 2 from same team)
            from collections import Counter
            team_counts = Counter(leg.player_prop.team for leg in parlay.legs)
            max_from_team = max(team_counts.values())
            assert max_from_team <= 2, "Max 2 players from same team"
            
            # Test confidence scores
            for leg in parlay.legs:
                assert 0 <= leg.confidence <= 100, "Leg confidence should be 0-100"
        
        print("✅ Parlay leg validation passed")
    
    @pytest.mark.asyncio
    async def test_odds_calculation(self):
        """Test parlay odds calculation"""
        parlays = await self.parlay_service.get_parlays(SportType.NFL)
        
        for parlay_response in parlays:
            parlay = parlay_response.parlay
            
            # Manually calculate odds to verify
            decimal_odds = 1.0
            for leg in parlay.legs:
                if leg.odds > 0:
                    decimal_odds *= (leg.odds / 100) + 1
                else:
                    decimal_odds *= (100 / abs(leg.odds)) + 1
            
            # Convert to American odds
            if decimal_odds >= 2.0:
                expected_odds = int((decimal_odds - 1) * 100)
            else:
                expected_odds = int(-100 / (decimal_odds - 1))
            
            # Allow for small rounding differences
            assert abs(parlay.total_odds - expected_odds) <= 10, "Odds calculation should be accurate"
        
        print("✅ Odds calculation validation passed")

class TestSystemIntegration:
    """Test end-to-end system integration"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.parlay_service = ParlayService()
    
    @pytest.mark.asyncio
    async def test_full_parlay_generation_flow(self):
        """Test complete parlay generation flow"""
        # Test both sports
        for sport in [SportType.NFL, SportType.MLB]:
            print(f"\n🧪 Testing {sport.value} parlay generation...")
            
            # Generate parlays for all tiers
            all_parlays = await self.parlay_service.get_parlays(sport)
            
            assert len(all_parlays) > 0, f"Should generate parlays for {sport.value}"
            
            # Test tier distribution
            tier_counts = {}
            for parlay_response in all_parlays:
                tier = parlay_response.parlay.tier
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
            
            print(f"   📊 Generated parlays by tier: {dict(tier_counts)}")
            
            # Test parlay response structure
            for parlay_response in all_parlays[:2]:  # Test first 2
                assert hasattr(parlay_response, 'parlay'), "Should have parlay object"
                assert hasattr(parlay_response, 'tier_requirements'), "Should have tier requirements"
                assert hasattr(parlay_response, 'analysis'), "Should have analysis"
                
                analysis = parlay_response.analysis
                required_analysis_fields = ['avg_confidence', 'expected_hit_rate', 'risk_assessment', 'recommendation']
                for field in required_analysis_fields:
                    assert field in analysis, f"Analysis should contain {field}"
        
        print("✅ Full integration test passed")
    
    @pytest.mark.asyncio
    async def test_refresh_functionality(self):
        """Test parlay refresh functionality"""
        # Get initial parlays
        initial_parlays = await self.parlay_service.get_parlays(SportType.NFL)
        initial_count = len(initial_parlays)
        
        # Trigger refresh
        await self.parlay_service.refresh_parlays(SportType.NFL)
        
        # Get refreshed parlays
        refreshed_parlays = await self.parlay_service.get_parlays(SportType.NFL)
        
        # Should have parlays after refresh
        assert len(refreshed_parlays) > 0, "Should have parlays after refresh"
        
        print(f"✅ Refresh test passed - {initial_count} -> {len(refreshed_parlays)} parlays")
    
    @pytest.mark.asyncio
    async def test_system_stats(self):
        """Test system statistics"""
        # Generate some parlays first
        await self.parlay_service.get_parlays(SportType.NFL)
        await self.parlay_service.get_parlays(SportType.MLB)
        
        # Get system stats
        stats = await self.parlay_service.get_system_stats()
        
        assert hasattr(stats, 'total_parlays_generated'), "Should have total parlays count"
        assert hasattr(stats, 'success_rate_by_tier'), "Should have success rates"
        assert hasattr(stats, 'average_confidence_by_tier'), "Should have average confidence"
        
        print(f"✅ System stats test passed - Generated: {stats.total_parlays_generated}")

def run_sample_outputs():
    """Display sample outputs for each tier"""
    async def show_samples():
        parlay_service = ParlayService()
        
        print("\n" + "="*80)
        print("📊 SAMPLE PARLAY OUTPUTS BY TIER")
        print("="*80)
        
        for sport in [SportType.NFL, SportType.MLB]:
            print(f"\n🏈 {sport.value} PARLAYS" if sport == SportType.NFL else f"\n⚾ {sport.value} PARLAYS")
            print("-" * 50)
            
            for tier in [TierType.FREE, TierType.PREMIUM, TierType.GOAT]:
                try:
                    parlays = await parlay_service.get_parlays(sport, tier)
                    
                    if parlays:
                        parlay_response = parlays[0]  # Show first parlay
                        parlay = parlay_response.parlay
                        analysis = parlay_response.analysis
                        
                        tier_emoji = {"FREE": "🎯", "PREMIUM": "💎", "GOAT": "🐐"}[tier.value]
                        
                        print(f"\n{tier_emoji} {tier.value} TIER")
                        print(f"Confidence: {parlay.overall_confidence:.1f}%")
                        print(f"Total Odds: {'+' if parlay.total_odds > 0 else ''}{parlay.total_odds}")
                        print(f"Expected Payout: {parlay.expected_payout:.1f}x")
                        print(f"Legs: {len(parlay.legs)}")
                        print(f"Risk: {analysis['risk_assessment']}")
                        
                        print("Top 3 Legs:")
                        for i, leg in enumerate(parlay.legs[:3], 1):
                            prop = leg.player_prop
                            print(f"  {i}. {prop.player_name} ({prop.team}) - "
                                  f"{prop.prop_type.value.replace('_', ' ').title()} "
                                  f"{leg.selection} {prop.line} ({leg.confidence:.1f}%)")
                    else:
                        print(f"\n{tier.value}: No parlays generated (strict requirements)")
                        
                except Exception as e:
                    print(f"\n{tier.value}: Error generating parlays - {str(e)}")
        
        await parlay_service.cleanup()
    
    asyncio.run(show_samples())

if __name__ == "__main__":
    # Run sample outputs
    run_sample_outputs()
    
    print("\n" + "="*80)
    print("🧪 RUNNING AUTOMATED TESTS")
    print("="*80)
    
    # Run pytest
    pytest.main([__file__, "-v"])
