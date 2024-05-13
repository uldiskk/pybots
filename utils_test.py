import utils

def testDummySum():
    assert utils.dummySum(1, 2) == 3

def testParametersGetter():
    fileName = "testDictionary.txt"
    testUrl = "https://dummy.com/lala?123/"
    testKeywordsArray = ['devops', 'dev ops']
    testFirstLocation = 1

    assert utils.getUrl(fileName) == testUrl
    assert utils.getKeywords(fileName) == testKeywordsArray
    assert utils.getBoolFirstLocation(fileName) == testFirstLocation