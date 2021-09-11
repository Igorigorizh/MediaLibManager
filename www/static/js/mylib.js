
/**
*
*  Base64 encode / decode
*  http://www.webtoolkit.info/
*
**/
 
var Base64 = {
 
	// private property
	_keyStr : "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",
 
	// public method for encoding
	encode : function (input) {
		var output = "";
		var chr1, chr2, chr3, enc1, enc2, enc3, enc4;
		var i = 0;
 
		input = Base64._utf8_encode(input);
 
		while (i < input.length) {
 
			chr1 = input.charCodeAt(i++);
			chr2 = input.charCodeAt(i++);
			chr3 = input.charCodeAt(i++);
 
			enc1 = chr1 >> 2;
			enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
			enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
			enc4 = chr3 & 63;
 
			if (isNaN(chr2)) {
				enc3 = enc4 = 64;
			} else if (isNaN(chr3)) {
				enc4 = 64;
			}
 
			output = output +
			this._keyStr.charAt(enc1) + this._keyStr.charAt(enc2) +
			this._keyStr.charAt(enc3) + this._keyStr.charAt(enc4);
 
		}
 
		return output;
	},
 
	// public method for decoding
	decode : function (input) {
		var output = "";
		var chr1, chr2, chr3;
		var enc1, enc2, enc3, enc4;
		var i = 0;
 
		input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");
 
		while (i < input.length) {
 
			enc1 = this._keyStr.indexOf(input.charAt(i++));
			enc2 = this._keyStr.indexOf(input.charAt(i++));
			enc3 = this._keyStr.indexOf(input.charAt(i++));
			enc4 = this._keyStr.indexOf(input.charAt(i++));
 
			chr1 = (enc1 << 2) | (enc2 >> 4);
			chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
			chr3 = ((enc3 & 3) << 6) | enc4;
 
			output = output + String.fromCharCode(chr1);
 
			if (enc3 != 64) {
				output = output + String.fromCharCode(chr2);
			}
			if (enc4 != 64) {
				output = output + String.fromCharCode(chr3);
			}
 
		}
 
		output = Base64._utf8_decode(output);
 
		return output;
 
	},
 
	// private method for UTF-8 encoding
	_utf8_encode : function (string) {
		string = string.replace(/\r\n/g,"\n");
		var utftext = "";
 
		for (var n = 0; n < string.length; n++) {
 
			var c = string.charCodeAt(n);
 
			if (c < 128) {
				utftext += String.fromCharCode(c);
			}
			else if((c > 127) && (c < 2048)) {
				utftext += String.fromCharCode((c >> 6) | 192);
				utftext += String.fromCharCode((c & 63) | 128);
			}
			else {
				utftext += String.fromCharCode((c >> 12) | 224);
				utftext += String.fromCharCode(((c >> 6) & 63) | 128);
				utftext += String.fromCharCode((c & 63) | 128);
			}
 
		}
 
		return utftext;
	},
 
	// private method for UTF-8 decoding
	_utf8_decode : function (utftext) {
		var string = "";
		var i = 0;
		var c = c1 = c2 = 0;
 
		while ( i < utftext.length ) {
 
			c = utftext.charCodeAt(i);
 
			if (c < 128) {
				string += String.fromCharCode(c);
				i++;
			}
			else if((c > 191) && (c < 224)) {
				c2 = utftext.charCodeAt(i+1);
				string += String.fromCharCode(((c & 31) << 6) | (c2 & 63));
				i += 2;
			}
			else {
				c2 = utftext.charCodeAt(i+1);
				c3 = utftext.charCodeAt(i+2);
				string += String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63));
				i += 3;
			}
 
		}
 
		return string;
	}
 
}




 function createRequestObject() {
  if (typeof XMLHttpRequest === 'undefined') {
    XMLHttpRequest = function() {
      try { return new ActiveXObject("Msxml2.XMLHTTP.6.0"); }
        catch(e) {}
      try { return new ActiveXObject("Msxml2.XMLHTTP.3.0"); }
        catch(e) {}
      try { return new ActiveXObject("Msxml2.XMLHTTP"); }
        catch(e) {}
      try { return new ActiveXObject("Microsoft.XMLHTTP"); }
        catch(e) {}
      throw new Error("This browser does not support XMLHttpRequest.");
    };
  }
  return new XMLHttpRequest();
}


function startProgressBar(){ 
//document.getElementById("search_result_frm").innerHTML = "<FORM action="" METHOD="POST" enctype='multipart/form-data' id="search_result_frm" > </FORM>"
//document.getElementById("loading").innerHTML = "<img src="../../image/ajax-loader.gif" />";
//document.all.loading.style.visibility="visible";
document.getElementById('loading').style.visibility="visible";
}
function stopProgressBar(){

//document.getElementById("loading").innerHTML = ""
// document.all.loading.style.visibility
document.getElementById('loading').style.visibility="hidden";
 }

function setAllOn(FormId) {
 
var pizzaForm = document.getElementById(FormId); 
if( pizzaForm == null  ) { return null; }
if ( pizzaForm.selector.value == 0){
 
        for (var i = 0; i < pizzaForm.length; i++) {
        var temp_el = pizzaForm[i];    
        if ( temp_el.type == 'checkbox' ){
                temp_el.checked = true;
        }
        }
        pizzaForm.selector.value = 1;
        }else{
 
for (var i = 0; i < pizzaForm.length; i++) {
        var temp_el = pizzaForm[i];    
        if ( temp_el.type == 'checkbox' ){
                temp_el.checked = false;
        }
        }
 
 
        pizzaForm.selector.value = 0;
 
}
}

function removeOptionSelected(id,value)
{
  var elSel = document.getElementById(id);
  var i;
  for (i = elSel.length - 1; i>=0; i--) {
    if (elSel.options[i].value == value) {
      elSel.remove(i);
    }
  }
}

function appendOptionLast(id,text,value)
{
  var elOptNew = document.createElement('option');
  elOptNew.text = text;
  elOptNew.value = value;
  var elSel = document.getElementById(id);

  try {
    elSel.add(elOptNew, null); // standards compliant; doesn't work in IE
  }
  catch(ex) {
    elSel.add(elOptNew); // IE only
  }
}

function do_send_json_req_general(json_req,url_part){
	req.open("POST", 'http://' + host + url_part, true)
	req.setRequestHeader('Content-Type', 'multipart/form-data','Pragma: no-cache','Expires: Mon, 26 Jul 1997 05:00:00 GMT','Cache-Control: no-store, no-cache, must-revalidate')

	
	req.onreadystatechange = processReqChange;
	//alert(json_req)
	req.send(json_req)
	//startProgressBar()

	return false;

}
