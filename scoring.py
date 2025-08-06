def score_confidence(predicted, prop_line):
    margin = abs(predicted - prop_line)
    if margin >= 5:
        return 'High'
    elif margin >= 2:
        return 'Medium'
    else:
        return 'Low'
