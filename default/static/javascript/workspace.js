Workspace = {
    code: {
    	size: function(size) {
    		frames["code"].window.setCodeSize(size);
    		var url = "/workspace/" + Workspace.id + "/update/int";
            jQuery.post(url, {field:"font_size", value:size, persist:"1"});
    	},
    	face: function(option) {
    	    var typeface_string = jQuery(option).attr("rel");
    		frames["code"].window.setCodeTypeface(typeface_string);
    		var url = "/workspace/" + Workspace.id + "/update/string";
    		jQuery.post(url, {field:"font_face", value:option.value, persist:"1"});
    	}
    },
    tabs: new function() {
        var current_tab = null;
        this.show = function(tab) {
            if (tab != current_tab) {
                if (tab != "styles") {
                    Workspace.styles.edit(null);
                }
                jQuery(".pane").hide();
                jQuery("#" + tab).show();
        		jQuery("#tool_tabs td").removeClass("current");
        		jQuery("#tool_tab_" + tab).addClass("current");
                var url = "/workspace/" + Workspace.id + "/update/string";
                jQuery.post(url, {field:"edit_tab", value:tab, persist:"1"});
                current_tab = tab;
            }
        };
    },
    frames: new function() {
        var loading = {};
        var current = "";
        this.loadingSpinner = function(onlyFor) {
            if (onlyFor === undefined || onlyFor == current) {
                jQuery("#spinner").show();
            }
        };
        this.reload = function(frame) {
            jQuery.each(jQuery.makeArray(frame), function(){
                frames[this].location.reload();
                loading[this] = true;
            });
        }
        this.loaded = function(frame) {
            loading[frame] = false;
            if (!loading[current]) {
                jQuery("#spinner").hide();
            }
        }
        this.switchTo = function(frame) {
            if (frame != current) {
                jQuery("#iframe_tabs .view_tab a").removeClass("view_tab_selected");
                jQuery("#tab_" + frame).addClass("view_tab_selected");
                jQuery("#main_container > iframe").hide();
                jQuery("#main_container #" + frame).show();
                current = frame;
                jQuery.post("/workspace/" + Workspace.id + "/update/string", {field:"view_tab", value:frame});
            }
        }
    },
    css: {
        load: function() {
            Workspace.frames.loadingSpinner("preview");
            var sample_stylesheet = jQuery("#select_loadcss").val();
            var url = "/workspace/" + Workspace.id + "/loadCSS";
            jQuery.post(url, {stylesheet:sample_stylesheet}, function(response){
                jQuery("#select_loadcss").get(0).selectedIndex = 0;
                jQuery("#css_text").val(response);
                Workspace.frames.reload("preview");
            });
        }
    },
    styles: new function() {
        var currently_editing = null;
        this.current = function() { return currently_editing; };
        this.edit = function(styleName) {
			var anchor = jQuery("#edit_style_" + styleName);
			jQuery("#style_list p a").removeClass("under_edit");
			anchor.addClass("under_edit");

			if (styleName) {
				jQuery("#style_edit").show();
				var parts = anchor.attr("rel").split("|");
				jQuery("#style_element").val(parts[0]);
				jQuery("#style_class").val(parts[1]);
				jQuery("#style_style").val(parts[2]);
			} else {
				jQuery("#style_edit").hide();
			}
			
			frames["code"].window.highlightStyle(styleName);
			frames["preview"].window.highlightStyle(styleName);
			currently_editing = styleName;				
	    };
		this.save = function() {
			if (currently_editing) {
			    var form = jQuery('#style_form');
			    var params = {
			        element: form.find("#style_element").val(),
			        css_class: form.find("#style_class").val(),
			        style: form.find("#style_style").val(),
			        name: currently_editing
			    };
				
				// Save clientside
				var pipestring = params["element"] + "|" + params["css_class"] + "|" + params["style"];
				jQuery("#edit_style_" + currently_editing).attr("rel", pipestring);
				
				// Save serverside
                Workspace.frames.loadingSpinner();
				var url = "/workspace/" + Workspace.id + "/save_style";
				jQuery.post(url, jQuery.param(params), function(){
                    Workspace.frames.reload(["code", "preview"]);
				});
			}
		};
		this.select = function(elt) {
		    Workspace.tabs.show("styles");
			this.edit(elt.title);
		};
    },
    urls: new function() {
		var current = null;
		
		this.edit = function(id) {
			if (id == current) return;

			// Highlight it in code view
			frames["code"].window.highlightLink(id);

			var divs = jQuery("#link_urls div");
			divs.removeClass("under_edit");
			
			// Fill in form
			if (id === null) {
				jQuery("#link_url_edit").val("");
				jQuery("#link_external_edit").attr("checked") = false;
				jQuery("#link_edit").css("visibility", "hidden");
			} else {
				var links = jQuery("#link_urls a");
				jQuery("#link_url_edit").val(links.eq(id).attr('href'));
				jQuery("#link_external_edit").attr("checked", links.eq(id).attr("target") == "_blank");
				divs.eq(id).addClass("under_edit");
				jQuery("#link_edit").css("visibility", "visible");
			}
			current = id;
		};
		
		this.save = function() {
			if (current !== null) {
                Workspace.frames.loadingSpinner();
				var div = jQuery("#link_urls div").eq(current);
				var a = div.find("a").eq(0);
				var warning = div.find("img").eq(0);
				a.attr("href", jQuery("#link_url_edit").val());
				a.attr("target", jQuery("#link_external_edit").is(":checked") ? "_blank" : null);

				this.updateValidityIcon(a, warning);

				// Update code view
				var url = "/workspace/" + Workspace.id + "/save_link";
				jQuery.post(url, {
					index: current,
					href: a.attr("href"),
					external: a.attr("target") == "_blank" ? "1" : "0"
				}, function(){
				    Workspace.frames.reload(["code", "preview"]);
				});
			}
		};
		
		this.saveBaseHref = function() {
		    Workspace.frames.loadingSpinner("preview");
			var val = jQuery("#base_href").val();
			if (val.length > 0 && val.charAt(val.length - 1) != "/") {
				jQuery("#base_href").val(jQuery("#base_href").val() + "/");
			}
			var url = "/workspace/" + Workspace.id + "/update/string";
			jQuery.post(url, {field:"base_href", value:jQuery("#base_href").val()}, function(){
			    Workspace.frames.reload("preview");
			});
		};
		
		this.updateValidityIcon = function(a, img) {
            var href = a.attr("href");
            var valid = false;
            if (/^http:|https:|ftp:|mailto:/.test(href)) valid = true;      // Absolute URL
            else if (/\/.+\//.test(href)) valid = true;                      // Slashes indicate a path
            else if (/\s|%20/.test(href)) valid = false;                     // Contains spaces
            else if (/^\//.test(href)) valid = true;                         // Rooted path
            else if (/^#/.test(href)) valid = true;                          // Anchor
            else if (/\w\.\w/.test(href)) valid = true;                      // File extension
            
            if (valid) {
                img.attr("src", "/static/images/link_ok.gif");
                img.attr("title", "");
            } else {
                img.attr("src", "/static/images/link_bad.gif");
                img.attr("title", "This link appears to have an invalid href.");
            }            
		}		
    },
	images: new function() {
		var current = null;
		
		this.edit = function(index) {
			if (index == current) return;		
			
			frames["code"].window.highlightImage(index);
			jQuery("#image_urls div").eq(current).removeClass("under_edit");

			// Fill in form
			if (index === null) {
				//$("image_src_edit").value = "";
				jQuery("#image_edit").css("visibility", "hidden");
			} else {
			    var link = jQuery("#image_urls div").eq(index).find("a");
                // var links = $("image_urls").getElementsByTagName("A");
                // var urls = links[index].getAttribute('href',2).split("|");
                // var embed = urls[0].split(".");
                // var target = links[index].target.split("|");
                // $("image_embed_edit").value = embed[0];
                // $("image_embed_extension").innerHTML = target[1] == "can_embed" ? ("." + embed[1]) : "";
                // $("image_src_edit").value = urls[1];
                // $("image_use_embedded_yes").checked = target[0] == "embed";
                // $("image_use_embedded_yes").disabled = target[1] != "can_embed";
                // $("image_use_embedded_no").checked = target[0] == "link";
                if (link.attr("use_external_url") == "True") {
                    jQuery("#image_use_embedded_no").attr("checked", true);
                } else {
                    jQuery("#image_use_embedded_yes").attr("checked", true);
                }
                var filename_parts = link.attr("filename").split(".");
                jQuery("#image_embed_edit").val(filename_parts[0]);
                jQuery("#image_embed_extension").text(filename_parts[1]);
                jQuery("#image_src_edit").val(link.attr("external_url"));
                jQuery("#image_alt").val(link.attr("alt"));
                jQuery("#image_urls div").eq(index).addClass("under_edit");
				jQuery("#image_edit").css("visibility", "visible");
				
			}
			current = index;			
		};
		
		this.save = function() {
			if (current !== null) {
			    Workspace.frames.loadingSpinner();
			    
				var a = jQuery("#image_urls div").eq(current).find("a");
				var external_url = jQuery("#image_src_edit").val();
				var use_embed = jQuery("#image_use_embedded_yes").is(":checked");
				var alt = jQuery("#image_alt").val();
				
				var url = "/workspace/" + Workspace.id + "/save_image";
				jQuery.post(url, {
				    index: current,
				    external_url: external_url,
				    use_external_url: use_embed ? "False" : "True",
				    alt: alt
				}, function() {
				    a.attr("alt", alt);
				    a.attr("use_external_url", use_embed ? "False" : "True");
				    a.attr("external_url", external_url);				    
				    Workspace.frames.reload(["code", "preview"]);
				});
			}			
		};
		
		this.savePath = function() {
		    Workspace.frames.loadingSpinner("code");
			var path = jQuery("#embedded_image_path").val();
			if (path.length > 0 && path.charAt(path.length - 1) != "/") {
				path += "/";
			}
			var url = "/workspace/" + Workspace.id + "/save_embedded_image_path";
			jQuery.post(url, {embedded_image_path: path}, function(){
			    Workspace.frames.reload("code");
			});
		}
		
	},
    initialize: function(id) {
        this.id = id;
        
        jQuery("#iframe_tabs .view_tab a").click(function(){
            Workspace.frames.switchTo(this.id.split("_")[1]);
            return false;
        });
        
        var update = function(field, value, format) {
            Workspace.frames.loadingSpinner();
            var url = "/workspace/" + id + "/update/" + format;
            jQuery.post(url, {field:field, value:value, persist:"1"}, function(response){
                Workspace.frames.reload(["code", "preview"]);
            });
            //jQuery.post(url, { field:field, value:value, persist:"1"});            
        }
        
        jQuery("input[type=checkbox][autosave]").click(function(){
            var field = jQuery(this).attr("name");
            var value = jQuery(this).is(":checked") ? "1" : "0";
            update(field, value, "bool");
        });
        
        jQuery("input[type=text][autosave]").change(function(){
            var field = jQuery(this).attr("name");
            var value = jQuery(this).val();
            var type = jQuery(this).attr("format") || "string";
            update(field, value, type);
        });
        
        jQuery("input[type=radio][autosave]").click(function(){
            var field = jQuery(this).attr("name");
            var value = jQuery(this).val();
            update(field, value, "string");
        });
        
        jQuery("select[autosave]").change(function(){
            var field = jQuery(this).attr("name");
            var value = jQuery(this).val();
            update(field, value, "string");
        });
        
	    jQuery("#tool_tabs a").click(function(){
		    Workspace.tabs.show(this.rel);
	        return false;
	    });
	    
	    jQuery("#code_preferences .size").change(function(){
	        Workspace.code.size(this.value);
	    });
	    jQuery("#code_preferences .face").change(function(){
	        var option = this.options[this.selectedIndex];
	        Workspace.code.face(option);
	    });
	    jQuery("#css_text").change(function(){
            Workspace.frames.loadingSpinner();
	        var css = jQuery(this).val();
	        var url = "/workspace/" + id + "/update/string";
	        jQuery.post(url, {field:"css", value:css, persist:"1"}, function(){
	            Workspace.frames.reload("preview");
	        });
	    });
    },
    popup: function(id) {
        var screen = jQuery("<div/>").css({
            /*backgroundColor:"white",
            opacity:0.7,*/
            position:"absolute",
            left:0,
            top:0,
            width: jQuery(window).width(),
            height: jQuery(window).height()
        });
        screen.click(function(){
            screen.remove();
            div.hide();
        });
        jQuery(document.body).append(screen);
        var div = jQuery("<div class='popup' />").css({
            width: 500
        });
        var content = jQuery("#" + id);
        content.find(".close").click(function(){
            screen.remove();
            div.hide();
        })
        div.append(content.show()).appendTo(document.body);
        div.css({
            left: (jQuery(window).width() - div.width()) / 2,
            top: (jQuery(window).height() - div.height()) * 0.333
        });
        div.click(function(e){
            e.stopPropagation();
        });
    }
};
