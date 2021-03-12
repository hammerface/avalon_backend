def retrieveParty(partySize, playerCount):
    # expose an endpoint that accepts a list, set 30s timer otherwise
    #make random party?
    response = [None] * partySize
    for i in range(0, len(response)):
        response[i] = i + 1
    
    if (len(response) != partySize):
        print('Given party is not the correct size')
    if (len(response) != len(set(response))):
        print('Given party members are not unique')
    if (not(all(isinstance(i, int) for i in response))):
        print('Given party list must contain only integers')
    if (not(all((0 <= i <= 9) for i in response))):
        print('Given party list contains numbers outside player range')

    return response
