document.addEventListener("DOMContentLoaded", function() {
  // check if any advanced filter check is selected on load and expand the
  // advanced section on page load
  var primaryWorkFilterValue = document.getElementById('primary_work_filter').value;

  if ($("#work-filter-form input:checkbox:checked").length > 0) {
    $('.collapse').collapse('show');

  } else if (primaryWorkFilterValue === 'only' || primaryWorkFilterValue === 'excl') {
    $('.collapse').collapse('show');
  }
});

document.querySelector("#work-filter-form").addEventListener("submit", function(e){
  // compare the dates provided and swap before form is submitted
  swapAssentDates();
  swapPublicationDates();
  swapRepealedDates();
  swapCommencementDates();
  swapAmendmentDates();
});

function checkAssentDate(){
  // if assent_date checkbox is clicked, make the dates required fields
  if (document.getElementById('assent_date_check').checked) {
    document.getElementById("assent_date_start").required = true;
    document.getElementById("assent_date_end").required = true;
  } else {
    document.getElementById("assent_date_start").required = false;
    document.getElementById("assent_date_end").required = false;      
  }
}

function checkPublicationDate(){
  // if publication _date checkbox is clicked, make the dates required fields
  if (document.getElementById('publication_date_check').checked) {
    document.getElementById("publication_date_start").required = true;
    document.getElementById("publication_date_end").required = true;
  } else {
    document.getElementById("publication_date_start").required = false;
    document.getElementById("publication_date_end").required = false;      
  }
}

function checkRepealDate(){
  // if repealed date checkbox is clicked, make the dates required fields
  if (document.getElementById('repealed_date_check').checked) {
    document.getElementById("repealed_date_start").required = true;
    document.getElementById("repealed_date_end").required = true;
  } else {
    document.getElementById("repealed_date_start").required = false;
    document.getElementById("repealed_date_end").required = false;      
  }
}

function checkCommencementDate(){
  // if commencement date checkbox is clicked, make the dates required fields
  if (document.getElementById('commencement_date_check').checked) {
    document.getElementById("commencement_date_start").required = true;
    document.getElementById("commencement_date_end").required = true;
  } else {
    document.getElementById("commencement_date_start").required = false;
    document.getElementById("commencement_date_end").required = false;      
  }
}

function checkAmendDate(){
  // if amendment date checkbox is clicked, make the dates required fields
  if (document.getElementById('amendment_date_check').checked) {
    document.getElementById("amendment_date_start").required = true;
    document.getElementById("amendment_date_end").required = true;
  } else {
    document.getElementById("amendment_date_start").required = false;
    document.getElementById("amendment_date_end").required = false;      
  }
}

// Date swapping
function swapDates(startDate, endDate){
  // This functions compares the start and end dates and swaps them accordingly
  if (new Date(startDate) > new Date(endDate)){
    return [endDate, startDate];
  } 
  return [startDate, endDate];
}

function swapAssentDates(){
  if (document.getElementById('assent_date_check').checked){
    var swappedDates = swapDates($('#assent_date_start').val(), $('#assent_date_end').val());

    $('#assent_date_start').val(swappedDates[0]);
    $('#assent_date_end').val(swappedDates[1]);
  }
}

function swapPublicationDates(){
  if (document.getElementById('publication_date_check').checked){
    var swappedDates = swapDates($('#publication_date_start').val(), $('#publication_date_end').val());

    $('#publication_date_start').val(swappedDates[0]);
    $('#publication_date_end').val(swappedDates[1]);
  }
}

function swapRepealedDates(){
  if (document.getElementById('repealed_date_check').checked){
    var swappedDates = swapDates($('#repealed_date_start').val(), $('#repealed_date_end').val());

    $('#repealed_date_start').val(swappedDates[0]);
    $('#repealed_date_end').val(swappedDates[1]);
  }
}

function swapCommencementDates(){
  if (document.getElementById('commencement_date_check').checked){
    var swappedDates = swapDates($('#commencement_date_start').val(), $('#commencement_date_end').val());

    $('#commencement_date_start').val(swappedDates[0]);
    $('#commencement_date_end').val(swappedDates[1]);
  }
}

function swapAmendmentDates(){
  if (document.getElementById('amendment_date_check').checked){
    var swappedDates = swapDates($('#amendment_date_start').val(), $('#amendment_date_end').val());

    $('#amendment_date_start').val(swappedDates[0]);
    $('#amendment_date_end').val(swappedDates[1]);
  }
}

