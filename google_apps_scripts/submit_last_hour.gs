// processes the last hour responses using our API
//
// author: Archy Nayoan
// email: archylefree.n@gmail.com


// change these values "XXXXXX", inside the quotations, to match yours
var surveyId = 'XXXXXX'; // change to your qualtrics survey's survey id
var token = 'XXXXXX'; // change to your qualtrics token
var dataCenter = 'ca1'; // change to your qualtrics data center, default: "ca1"


function processLastHour() {

  var method = 'submit_last_hour';
  var url = 'https://backend-dot-cits-3200.appspot.com/' + method + '?survey_id=' + surveyId + '&token=' + token + '&data_center=' + dataCenter;
  var params = {
    'method' : 'post',
    'contentType': 'application/x-www-form-urlencoded'
  };

  Logger.log(UrlFetchApp.fetch(url, params));
}
