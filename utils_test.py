import utils

def testDummySum():
    assert utils.dummySum(1, 2) == 3

def testParametersGetter():
    fileName = "testFiles/testDictionary.txt"
    testUrl = "https://dummy.com/lala?123/"
    testKeywordsArray = ['devops', 'dev ops']
    testFirstLocation = 1
    testGeoLocation = '%5B"106491660"%5D'
    testMessage = '''text text

📅test!'''

    assert utils.getUrl(fileName) == testUrl
    assert utils.getKeywords(fileName) == testKeywordsArray
    assert utils.getBoolFirstLocation(fileName) == testFirstLocation
    assert utils.getMessageText(fileName) == testMessage
    assert utils.getGeoLocation(fileName) == testGeoLocation

def testWorkWithDB():
    fileOfExcludedNames = "testFiles/testExcluded.txt"
    fileOfNamesToAppend = "testFiles/testAppend.txt"
    testExcludeArray = ['name1', 'namename2']
    testAppendedArray = ['name1', 'namename2', 'name3', 'namenamename4']

    excludeList = utils.getExcludeList(fileOfExcludedNames, 1, 0)
    assert excludeList == testExcludeArray

    excludeList = utils.appendListFromFileToList(excludeList, fileOfNamesToAppend)
    assert excludeList == testAppendedArray

