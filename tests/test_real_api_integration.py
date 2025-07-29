"""
Integration tests for real sports data API
Run these tests after setting up real API keys
"""
import asyncio
import pytest
from src.services.sports_data_service import SportsDataService
from src.models.parlay import SportType


class TestRealAPIIntegration:
    """Tests for real SportsDataIO API integration"""
    
    @pytest.mark.asyncio
    async def test_api_connectivity(self):
        """Test basic API connectivity with real credentials"""
        service = SportsDataService()
        
        # Skip test if no API key configured
        if not service.api_key or service.api_key == "demo_key":
            pytest.skip("No real API key configured - using mock data")
        
        try:
            props = await service.fetch_player_props(SportType.MLB)
            assert len(props) > 0, "Should return at least one prop"
            print(f"✅ Successfully fetched {len(props)} MLB props")
        except Exception as e:
            pytest.fail(f"API connectivity test failed: {e}")
        finally:
            await service.close_session()
    
    @pytest.mark.asyncio
    async def test_data_structure_validation(self):
        """Validate that API response matches expected structure"""
        service = SportsDataService()
        
        if not service.api_key or service.api_key == "demo_key":
            pytest.skip("No real API key configured")
        
        props = await service.fetch_player_props(SportType.MLB)
        
        # Validate required fields exist
        required_fields = ['player_name', 'team', 'prop_type', 'line']
        for prop in props[:3]:  # Check first 3 props
            for field in required_fields:
                assert field in prop, f"Missing required field: {field}"
        
        await service.close_session()
    
    @pytest.mark.asyncio  
    async def test_multiple_sports(self):
        """Test fetching data for different sports"""
        service = SportsDataService()
        
        if not service.api_key or service.api_key == "demo_key":
            pytest.skip("No real API key configured")
        
        try:
            mlb_props = await service.fetch_player_props(SportType.MLB)
            nfl_props = await service.fetch_player_props(SportType.NFL)
            
            print(f"✅ MLB props: {len(mlb_props)}")
            print(f"✅ NFL props: {len(nfl_props)}")
            
            # At least one sport should have props
            assert len(mlb_props) > 0 or len(nfl_props) > 0
            
        finally:
            await service.close_session()


# Manual test function for development
async def manual_api_test():
    """
    Manual test function for development - run this to test API integration
    Usage: python -c "import asyncio; from tests.test_real_api import manual_api_test; asyncio.run(manual_api_test())"
    """
    print("🔄 Testing real API integration...")
    
    service = SportsDataService()
    
    if not service.api_key or service.api_key == "demo_key":
        print("⚠️  No real API key found - system will use mock data")
        print("   Set SPORTSDATAIO_API_KEY in .env file for real data")
    else:
        print(f"✅ API key configured: {service.api_key[:8]}...")
    
    try:
        # Test MLB props
        print("\n🔄 Fetching MLB props...")
        mlb_props = await service.fetch_player_props(SportType.MLB)
        print(f"✅ Fetched {len(mlb_props)} MLB props")
        
        if mlb_props:
            sample_prop = mlb_props[0]
            print(f"   Sample prop: {sample_prop.get('player_name')} - {sample_prop.get('prop_type')}")
        
        # Test NFL props
        print("\n🔄 Fetching NFL props...")
        nfl_props = await service.fetch_player_props(SportType.NFL)
        print(f"✅ Fetched {len(nfl_props)} NFL props")
        
        if nfl_props:
            sample_prop = nfl_props[0]
            print(f"   Sample prop: {sample_prop.get('player_name')} - {sample_prop.get('prop_type')}")
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
    finally:
        await service.close_session()
        print("\n✅ API integration test complete")


if __name__ == "__main__":
    asyncio.run(manual_api_test())
