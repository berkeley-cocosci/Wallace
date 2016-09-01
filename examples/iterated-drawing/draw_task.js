//
// Draw a set of characters.
//  This accepts either completion canvases or regular canvases 
//
// DATA structure (passed to load.images())
//  data.imglist_target: list of file names to target images
//  data.imglist_complete (optional)
//  data.show_side (if we have data.imglist_complete, which can be either left,right,top,bottom)
//
// HTML parameters accepted:
//
//   ntrials: (number) number of trials
//  
//  from super_task
//
//   exclude: (string) aaa,bbb,ccc,...   a list if comma-separated strings of workerIds to exclude as subjects
//   workerId: (string) workedId (as supplied by turk)
//   condition: (string) manually set condition of experiment (otherwise random)
//   debug: (true/false) if true, print data to the browser rather than to turk
//   skip_quiz: (true/false) if true, skip the quiz of the instructions
//   skip_survey: (true/false) if true, skip the survey at the end
//
//  spec accepted:
//
//   spec.size_imgs: size of images in pixels
//  from super_task
//   spec.list_condition: must be an array of strings naming the possible conditions
//
var draw_task = function (spec,my) {
	
	// PRIVATE VARIABLES
	var that = {};
	my = my || {};
	
	that = super_task(spec,my);
		
	var super_check_survey = my.superior('check_survey'); 
	var super_print_data_to_form = my.superior('print_data_to_form');
	var super_start_main_exp = my.superior('start_main_exp');
	
	my.num_trials; // number of images
	my.imgs_target;
	my.imgs_complete;
	my.size_imgs = spec.size_imgs || 105; // size of the images
	my.preloader = []; // image loading object
	my.list_canvas = new Array();
	my.ntrials_override;
	my.has_complete = false; // completion drawings, or just drawings?
	my.show_side; // left,right,bottom,top 	
	my.pre = 'pre'; // 
	my.div_pload = 'pload'; // display percent of images loaded here
	my.div_demo_canvas = 'demo'; // div id for demo canvas
	my.div_exp_body = 'exp_body'; // div id
	my.class_ntrials = 'ntrials';
	my.div_button_to_quiz = 'toquiz';

	// override parameters
	my.skip_quiz = true;
	my.skip_survey = true;
	my.debug_mode = true;
	
	// constructor
	(function () {		
		// process URL parameters
		if (my.url.param('ntrials') !== undefined) {
   			my.ntrials_override = parseInt(my.url.param('ntrials')); // override for how many trials
		}
	})();
	
	my.start_main_exp = function () {
    	super_start_main_exp();
    	my.display_canvases();
    };
			
	// display canvases in the main experiment
	my.display_canvases = function () {		
		for (var i=0; i<my.num_trials; i++) {
			if (my.has_complete) {
				my.list_canvas[i] = canvasobj(i+'',my.imgs_target[i],my.imgs_complete[i],my.show_side);
			}
			else {
				my.list_canvas[i] = canvasobj(i+'',my.imgs_target[i]);	
			}
			var mydom = my.list_canvas[i].getDOMelem();
    		$('#'+my.div_exp_body).append(mydom);
		}		
	};
	
	// check if all of the canvases have some content on them
	my.check_full_canvases = function () {
		for (var i=0; i<my.list_canvas.length; i++) {
			if (my.list_canvas[i].isEmpty()) {
				return false;
			}
		}
		return true;		
	};

	// check survery for completion
    my.check_survey = function () {
    	if ( tu.emptyField('survey_radio_handed',my.list_survey_radio)
    	  || tu.emptyField('survey_txt_native_lang',my.list_survey_txt)
    	  || tu.emptyField('survey_txt_country',my.list_survey_txt)
    	  || tu.emptyField('survey_radio_use_hand',my.list_survey_radio)
    	  || tu.emptyField('survey_radio_device',my.list_survey_radio) ) {
			 alert('A required field is still empty.');
			 return false;
		}
		return super_check_survey();		
	};
	
	// input has_border: (boolean) should image has a border? (default=false)
	my.resize_and_protect = function (image_objects,size_img,has_border) {
		image_objects = tu.protectImages(image_objects);
		$(image_objects).attr('width',size_img).attr('height',size_img);
		if (has_border) {
			$(image_objects).attr('class','image_border');	
		}
		return image_objects;		
	};
	
	// display the percent of images loaded
	my.display_perc_loaded = function (perc) {
		$('#'+my.div_pload).html(perc);
	};
	
	// display failure in loading
	my.display_load_error = function () {
		var str = 'I am very sorry, there was an error loading the images. Please email <b>brenden@mit.edu</b> to report this problem.';
		$('#'+my.pre).html(str);
		tu.changeDisplay('',my.div_class);
	};
	
	// turn on the "to quiz" button
	my.quiz_button_on = function () {
		var imgs = my.preloader.get_images();
		if (my.has_complete) {
			my.imgs_target = imgs[0];
			my.imgs_complete = imgs[1];
			my.imgs_target = my.resize_and_protect(my.imgs_target,my.size_imgs);
			my.imgs_complete = my.resize_and_protect(my.imgs_complete,my.size_imgs);
		}
		else {
			my.imgs_target = imgs;
			my.imgs_target = my.resize_and_protect(my.imgs_target,my.size_imgs);
		}		
		// show demo
		if (my.has_complete) {
			var demo_canvas = canvasobj('demo',my.imgs_target[0],my.imgs_complete[0],my.show_side);			
		}
		else {
			var demo_canvas = canvasobj('demo',my.imgs_target[0]);	
		}		
		$('#'+my.div_demo_canvas).append(demo_canvas.getDOMelem());
		$('#'+my.div_button_to_quiz).attr('style',''); // unhide the button to proceed
	};

	// print the results of the experiment
	my.print_data_to_form = function () {
		my.txt = my.txt + tu.printListCanvas(my.list_canvas);
		super_print_data_to_form();
	};	
	
	// contains data.imglist_target, data.imglist_complete (optional), data.show_side (if we have data.imglist_complete)
	that.load_images = function (data) {
		if (data.imglist_complete) {
			my.has_complete = true;
			if (data.show_side === undefined) {
				throw new Error('missing data.show_side if this is a completion task');
			}
			my.show_side = data.show_side;
		}		
		var len = data.imglist_target.length;
		if (my.has_complete) {
			if (len !== data.imglist_complete.length) {
				throw new Error('image lists are not the same length');
			}	
		}		
		my.num_trials = len;
		if (my.ntrials_override > 0) {
			if (my.ntrials_override > my.num_trials) {    			
    			var str = 'URL parameter ntrials: the maximum number of trials is ' + my.num_trials;
    			my.throw_error(str);
    		}
    		my.num_trials = my.ntrials_override;		
    	}
		$('.'+my.class_ntrials).html(my.num_trials);
		
		// apply permutation
		var perm = tu.randperm(0,len-1);
		data.imglist_target = tu.apply_perm(data.imglist_target,perm);
		if (my.has_complete) {
			data.imglist_complete = tu.apply_perm(data.imglist_complete,perm);
		}
				
		if (my.has_complete) {		
			var grandlist = [data.imglist_target, data.imglist_complete];
		}
		else {
			var grandlist = data.imglist_target;
		}		
		my.preloader = image_preloader(grandlist,my.quiz_button_on,my.display_load_error,my.display_perc_loaded);		
	};
	
	that.finished_drawing = function () {
    	if (!my.check_full_canvases()) {
    		alert('Not all drawings are completed.');
    	}
    	else {
    		that.load_survey();
    	}
    };

	return that;
};