function switchDisplay(id) {

    if(document.getElementById) {
       // DOM
       var element = document.getElementById(id);
    } else {
        if(document.all) {
            // Proprietary DOM
            var element = document.all[id];
        } else {
            // Create an object to prevent errors further on
            var element = new Object();
        }
    }

    if(!element) {
        /* The page has not loaded or the browser claims to support
        document.getElementById or document.all but cannot actually
        use either */
        return;
    }

    // Reference the style ...
    if (element.style) {
        style = element.style;
    }

    if (typeof(style.display) == 'undefined' &&
        !( window.ScriptEngine && ScriptEngine().indexOf('InScript') + 1 ) ) {
        //The browser does not allow us to change the display style
        //Alert something sensible (not what I have here ...)
        window.alert( 'Your browser does not support this' );
        return;
    }

   // Change the display style
    if (style.display == 'none') {
        style.display = '';
        switchImage(id, 'harrow.png', 'varrow.png');
   }
    else {
        style.display = 'none'
        switchImage(id, 'varrow.png', 'harrow.png');
    }
}

function switchImage(id, oldname, newname) {
    if(document.getElementById) {
       // DOM
       var element = document.getElementById(id+'.arrow');
    } else {
       // Proprietary DOM
       var element = document.all[id+'.arrow'];
    }
    element.src = element.src.replace(oldname, newname);
}

/*
search in list of hrefs to avoid requests to the backend

*/
var found_sets = new Array();   // init a global array that holds lists for
							  // found elements

function getSearchResult(searchtext)
	{
	if (searchtext.length == 0) found_sets = new Array();
 	var searchindex = searchtext.length - 1;

 	// process backspace i.e search string gets shorter
	if (found_sets.length > searchindex)
	{  rubbish = found_sets.pop();
	   var idlist = found_sets[searchindex];
	   for (var n = 0 ; n < idlist.length ; n++)
	   {
	     element = document.getElementById(idlist[n]);
	     element.style.display='block';
	   }
	   return;
	}

	var reslist = document.getElementById('resultlist');
	var children = reslist.getElementsByTagName('div') //reslist.childNodes;
    var element;
	var subelement;
	var refelement;
	var comparetext;
	var compareresult;
	var resultarray = new Array();
	var itemcount = 0;
	for (var n = 0 ; n < children.length ; n++)
	{
		element = children[n];                          // get one div element
	    element.style.display='none' ;                  // reset visibility
	    subelement = element.getElementsByTagName('a'); // get list of a subelements
	    refelement = subelement[0];                     // get one a element
	    comparetext = refelement.firstChild.nodeValue;  // get textnode of a element
	    compareresult = comparetext.search(searchtext);

		if (compareresult != -1)
		   {element.style.display='block';
		    resultarray[itemcount] = element.getAttribute("id");
		    itemcount = itemcount + 1;
		   }
	}
	found_sets[searchindex] = resultarray;
	}

function simplegetSearchResult(searchtext)
	{

	var searchindex = searchtext.length - 1;

	var reslist = document.getElementById('resultlist');
	var children = reslist.getElementsByTagName('div') //reslist.childNodes;
    var element;
	var subelement;
	var refelement;
	var comparetext;
	var compareresult;
	for (var n = 0 ; n < children.length ; n++)
		{
		element = children[n];                          // get one div element
	    element.style.display='none'                    // reset visibility
	    subelement = element.getElementsByTagName('a'); // get list of a subelements
	    refelement = subelement[0];                     // get one a element
	    comparetext = refelement.firstChild.nodeValue;  // get textnode of a element
	    compareresult = comparetext.search(searchtext);
		if (compareresult != -1)
		   {element.style.display='block';}

		}
}

/*
Do tree collapsing and expanding by setting table row elements style display to
none or block and set the images appropriate


*/
function treeClick(treeid) {

    var prent = document.getElementById(treeid).parentNode;
    var children = prent.getElementsByTagName('tr');
    var found = 0;
    var action = "block";
    var treeiddepth = 0;

    for (var n = 0; n < children.length; n++) {
         var element = children[n];
         if (found==1) {
             if ( treeiddepth < element.getAttribute("treedepth") ) {
                        element.style.display = action;
	                var elid = element.getAttribute("id");
	                if (document.getElementById("i"+elid) != null) {
			            var subimg = document.getElementById("i"+elid)

			if (action=="none" && subimg.src.search('minus') != -1) {
		             subimg.src = subimg.src.replace('minus', 'plus');
			}
	                if (action=="block" && subimg.src.search('plus') != -1) {
		             subimg.src = subimg.src.replace('plus', 'minus');
			}
			}
		     } else {
		         return;
		     }
	         }
	         if (element.getAttribute("id")==treeid) {
	             found = 1;
	             treeiddepth = element.getAttribute("treedepth")
	             var img = document.getElementById("i"+treeid);
	             if (img.src.search('minus') != -1) {
		         img.src = img.src.replace('minus', 'plus');
	                 action="none";
		     } else {
		         img.src = img.src.replace('plus', 'minus');
	                 action="block";
		     }
		 }
	   }
}
