var task;

// Initialize the experiment
$(document).ready(function() {
	
	// Parameters
	var nchar = 10; // number of unique character images
	
	var spec = {};
	spec.list_condition = ['default'];	
	task = draw_task(spec);

	var data = {};
	data.imglist_target = targetlist(nchar,1);	
	task.load_images(data);
});

// Specifies the file names for the characters we want to include
var targetlist = function (nchar,start_count) {
	var list = new Array();
    var dname = 'characters/';
    var bname = 'handwritten';
    var count = 0;
	for (var c=start_count; c <= nchar+start_count-1; c++) {
       	str = dname + bname + c + '.png';
       	list[count] = str;
       	count ++;
    }
    return list;
};