    var Renderer = function(canvas)
    {
        var canvas = $(canvas).get(0);
        var ctx = canvas.getContext("2d");
		var gfx = arbor.Graphics(canvas);
        var particleSystem;

        var that = {
            init:function(system){
                //начальная инициализация
                particleSystem = system;
                particleSystem.screenSize(canvas.width, canvas.height); 
                particleSystem.screenPadding(80);
                that.initMouseHandling();
            },
      
            redraw:function(){
                //действия при перересовке
                ctx.fillStyle = "white";    //белым цветом
                ctx.fillRect(0,0, canvas.width, canvas.height); //закрашиваем всю область
            
                particleSystem.eachEdge(    //отрисуем каждую грань
                    function(edge, pt1, pt2){   //будем работать с гранями и точками её начала и конца
                        ctx.strokeStyle = "rgba(0,0,0, .333)";  //грани будут чёрным цветом с некой прозрачностью
                        ctx.lineWidth = 1;  //толщиной в один пиксель
                        ctx.beginPath();        //начинаем рисовать
                        ctx.moveTo(pt1.x, pt1.y); //от точки один
                        ctx.lineTo(pt2.x, pt2.y); //до точки два
                        ctx.stroke();
                });
    
                particleSystem.eachNode(    //теперь каждую вершину
                    function(node, pt){     //получаем вершину и точку где она
						//alert(node.data.w)
                        
                        ctx.fillStyle = node.data.color;   //с его цветом понятно
			var label = node.data.label
			//	var w = label.toString().length*5;         //ширина квадрата
			var node_name_len = Math.max(20, 20+gfx.textWidth(label) )
			//alert(gfx.textWidth(label))
			var w = node.data.w
						
			if (w == 0){
				w = node_name_len
			}
			if (node.data.mult_line){
				if (node.data.mult_line == "X"){
					w = Math.max(20, 20+6*w )
				}
			}

			if (node.data.shape == "dot"){
				gfx.oval(pt.x-w/2, pt.y-w/2, w+5,w+5, {fill:ctx.fillStyle})
                                //gfx.oval(pt.x+w/2, pt.y, w+5,w+5, {fill:ctx.fillStyle})


				var label_array = label.split("$%")						

				for (i=0;i<label_array.length;i++){
					gfx.text(label_array[i], pt.x+5, pt.y+i*12, {color:node.data.font_color, align:"center", font:"Arial", size:12})
				}
	
				}
			else if(node.data.shape == "box"){

				var label_array = label.split("$%")						
				gfx.rect(pt.x-w/2, pt.y-20, w+10,20*label_array.length, 4, {fill:ctx.fillStyle})

				for (i=0;i<label_array.length;i++){
				gfx.text(label_array[i], pt.x+5, pt.y+i*12, {color:node.data.font_color, align:"center", font:"Arial", size:12})
				}

			
						
			}else{
				ctx.fillStyle = node.data.color
				var label_array = label.split("$%")	
				gfx.rect(pt.x-w/2, pt.y-10, w+10,20*label_array.length, 4, {fill:ctx.fillStyle})

				for (i=0;i<label_array.length;i++){
					gfx.text(label_array[i], pt.x+5, pt.y+i*12, {color:node.data.font_color, align:"center", font:"Arial", size:12})
				}
		
			}
						
                        //ctx.fillStyle = "black";    //цвет для шрифта
                        //ctx.font = '13px sans-serif'; //шрифт
                        //ctx.fillText (node.name, pt.x+8, pt.y+8); //пишем имя у каждой точки
						
						
						if (!(label||"").match(/^[ \t]*$/)){
							pt.x = Math.floor(pt.x)
							pt.y = Math.floor(pt.y)
						}else{
							label = null
						  }
			//ctx.fillText(label||"", pt.x, pt.y+4)  
						
                });             
            },
        
            initMouseHandling:function(){   //события с мышью
                var dragged = null;         //вершина которую перемещают
                var handler = {
                    clicked:function(e){    //нажали
                        var pos = $(canvas).offset();   //получаем позицию canvas
                        _mouseP = arbor.Point(e.pageX-pos.left, e.pageY-pos.top); //и позицию нажатия кнопки относительно canvas
                        dragged = particleSystem.nearest(_mouseP);  //определяем ближайшую вершину к нажатию
                        if (dragged && dragged.node !== null){
                            dragged.node.fixed = true;  //фиксируем её
				
				if (dragged.node.data.node_type){
				
				if (dragged.node.data.node_type == "center"){
					//Эта инструкция по непонятной причини имеет в данном контексте кокорректное поведение и вызывает краткое подвисание плеера. врезультате чего возвращается ошибка
					//var req = "{"+"\""+"player_control"+"\""+":"+"\""+"pause"+"\""+"}"
					
					//alert(req)			
			
					//do_send_json_req_general(req,"/medialib/graf/")
				}
				else if(dragged.node.data.node_type == "leaf_navi"){
				 if (dragged.node.data.play_tag){
					var req = "{"+"\"" +"navigation_control"+"\""+":"+"\""+"goto_tagL"+"\""+","+"\""+"force_play"+"\""+":"+"1"+","+"\""+"sel_idL"+"\""+":["+dragged.node.data.play_tag.toString()+"]}"
					//alert(req)
					do_send_json_req_general(req,"/medialib/graf/")
					

				}

				}

				//alert( dragged.node.data.link)					
				//$.post(dragged.node.data.link,{"player_control":"pause"})
				}
						
			   //alert( dragged.node.data.tag_id)					
                        }
                        $(canvas).bind('mousemove', handler.dragged);   //слушаем события перемещения мыши
                        $(window).bind('mouseup', handler.dropped);     //и отпускания кнопки
                        return false;
                    },
                    dragged:function(e){    //перетаскиваем вершину
                        var pos = $(canvas).offset();
                        var s = arbor.Point(e.pageX-pos.left, e.pageY-pos.top);
    
                        if (dragged && dragged.node !== null){
                            var p = particleSystem.fromScreen(s);
                            dragged.node.p = p; //тянем вершину за нажатой мышью
                        }
    
                        return false;
                    },
                    dropped:function(e){    //отпустили
                        if (dragged===null || dragged.node===undefined) return; //если не перемещали, то уходим
                        if (dragged.node !== null) dragged.node.fixed = false;  //если перемещали - отпускаем
                        dragged = null; //очищаем
                        $(canvas).unbind('mousemove', handler.dragged); //перестаём слушать события
                        $(window).unbind('mouseup', handler.dropped);
                        _mouseP = null;
                        return false;
                    }
                }
                // слушаем события нажатия мыши
                $(canvas).mousedown(handler.clicked);
            },
      
        }
        return that;
    }

 function  visMediLibGraf(grf_data){
	var sys = arbor.ParticleSystem(1000); // создаём систему
     sys.parameters({gravity:true}); // гравитация вкл
     sys.renderer = Renderer("#viewport") //начинаем рисовать в выбраной области
	 $.each(grf_data.nodes, function(i,node){
						
						 sys.addNode(node.name,node.data); //добавляем вершину
						});
						
	$.each(grf_data.edges, function(i,edge){
		 sys.addEdge(sys.getNode(edge.src),sys.getNode(edge.dest)); //добавляем грань
	});
}

 function  visMediLibGraf_at_once(grf_data,canvas_id){
	 var sys = arbor.ParticleSystem(1000); // создаём систему
     sys.parameters({gravity:true}); // гравитация вкл
	 
     sys.renderer = Renderer(canvas_id) //начинаем рисовать в выбраной области
	 //sys.prune(function(node, from, to){return true;});
	//sys.graft(grf_data)
    return sys	
	
}

//jQuery(function($){
//    visMediLibGraf.init();
//});    