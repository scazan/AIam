var Warper = function() {
	this.warpTarget;
	this.warping=false;
	this.controlPoints = [];
	this.warpDataOriginal = {};
	this.aspect = {};
	this.radius = 13;
	this.loadedWarpData = '';

	getTransform = function(from, to) {
		var A, H, b, h, i, k_i, lhs, rhs, _i, _j, _k, _ref;
		console.assert((from.length === (_ref = to.length) && _ref === 4));
		A = [];
		for (i = _i = 0; _i < 4; i = ++_i) {
		  A.push([from[i].x, from[i].y, 1, 0, 0, 0, -from[i].x * to[i].x, -from[i].y * to[i].x]);
		  A.push([0, 0, 0, from[i].x, from[i].y, 1, -from[i].x * to[i].y, -from[i].y * to[i].y]);
		}
		b = [];
		for (i = _j = 0; _j < 4; i = ++_j) {
		  b.push(to[i].x);
		  b.push(to[i].y);
		}
		h = numeric.solve(A, b);
		H = [[h[0], h[1], 0, h[2]], [h[3], h[4], 0, h[5]], [0, 0, 1, 0], [h[6], h[7], 0, 1]];
		for (i = _k = 0; _k < 4; i = ++_k) {
		  lhs = numeric.dot(H, [from[i].x, from[i].y, 0, 1]);
		  k_i = lhs[3];
		  rhs = numeric.dot(k_i, [to[i].x, to[i].y, 0, 1]);
		  console.assert(numeric.norm2(numeric.sub(lhs, rhs)) < 1e-9, "Not equal:", lhs, rhs);
		}
		return H;
	};

	applyTransform = function(element, originalPos, targetPos, callback) {
	    var H, from, i, j, p, to;
	    from = (function() {
	      var _i, _len, _results;
	      _results = [];
	      for (_i = 0, _len = originalPos.length; _i < _len; _i++) {
	        p = originalPos[_i];
	        _results.push({
	          x: p[0] - originalPos[0][0],
	          y: p[1] - originalPos[0][1]
	        });
	      }
	      return _results;
	    })();
	    to = (function() {
	      var _i, _len, _results;
	      _results = [];
	      for (_i = 0, _len = targetPos.length; _i < _len; _i++) {
	        p = targetPos[_i];
	        _results.push({
	          x: p[0] - originalPos[0][0],
	          y: p[1] - originalPos[0][1]
	        });
	      }
	      return _results;
	    })();
	    H = getTransform(from, to);
	    
	    $(element).css({
	      'transform': "matrix3d(" + (((function() {
	        var _i, _results;
	        _results = [];
	        for (i = _i = 0; _i < 4; i = ++_i) {
	          _results.push((function() {
	            var _j, _results1;
	            _results1 = [];
	            for (j = _j = 0; _j < 4; j = ++_j) {
	              _results1.push(H[j][i].toFixed(20));
	            }
	            return _results1;

	          })());
	        }
	        return _results;
	      })()).join(',')) + ")",
	      'transform-origin': '0 0'
	    });          
	    return typeof callback === "function" ? callback(element, H) : void 0;
	};

	///event
	var that = this;
	// that.init();

	this.warperKeyDownListener = function (event) {
		console.debug(event.keyCode);

		if (event.keyCode == 87 && event.shiftKey == true) { // Shift+W to edit
			if (that.warping == false) {
				that.warping=true;
				that.warpTarget.addClass('editwarp');
				that.showControlPoints(true);
				that.makeTransformable(that.warpTarget);
			} else {
				that.warpTarget.removeClass('editwarp');
				that.showControlPoints(false);
				that.warping = false;
			}
			console.debug("shift + W");
		}

		if (that.warping == true) {
			if (event.keyCode >= 37 && event.keyCode <= 40) { // arrow keys to move warp point pairs
				var warpData = that.getWarpData();
				warpData = that.moveWarpData(event, warpData);
				that.setWarpData(warpData);
			}
			if (event.keyCode == 82) { // r key to reset
				that.applyTransform(that.warpDataOriginal)
				that.setWarpData(that.warpDataOriginal);
				var warpDataArray = that.warpDataToArray(that.warpDataOriginal);
				applyTransform(that.warpTarget, warpDataArray, warpDataArray);
			}
			if (event.keyCode == 13) { // enter to save
				that.saveWarpData('warping.json', that.getWarpData());
			}
		}
	};

	this.showControlPoints = function (show) {
		console.log(this.controlPoints.length)
		for (var _i = 0, _len = this.controlPoints.length; _i < _len; _i++) {
			console.log(_i)

			if (show)
				$(this.controlPoints[_i]).css('visibility', 'visible');
			else
				$(this.controlPoints[_i]).css('visibility', 'hidden');
		}
	};

	this.moveWarpData = function (event, warpData) {
		var offset = this.getWarpDataOffset(event);

		if (event.ctrlKey == false) {
			warpData = this.moveWarpDataOffset(warpData, offset);
		}
		else {
			warpData = this.moveWarpDataOffsetAspect(warpData, offset);
		}

		return warpData;
	};

	this.moveWarpDataOffset = function (warpData, offset) {
		for (var element in warpData) {
			warpData[element].left += offset.left;
			warpData[element].top += offset.top;
		}

		return warpData;
	}

	this.moveWarpDataOffsetAspect = function (warpData, offset) {
		warpData.warpPointRightTop.left += offset.left;
		warpData.warpPointRightBottom.left += offset.left;

		var newWidth = this.getWarpDataWidth(warpData);
		var newHeight = newWidth / this.aspect;

		warpData.warpPointLeftBottom.top = warpData.warpPointLeftTop.top + newHeight;
		warpData.warpPointRightBottom.top = warpData.warpPointLeftTop.top + newHeight;

		return warpData;
	}

	this.getWarpDataOffset = function( event ) {
		var offset = { 
			left: 0,
			top: 0
		};

		if ( event.ctrlKey == false ) {
			if (event.keyCode == 37) { offset.left = -1; } // left arrow
			else if (event.keyCode == 38) { offset.top = -1; } // up arrow
			else if (event.keyCode == 39) { offset.left = 1; } // right arrow
			else if (event.keyCode == 40) { offset.top = 1; } // bottom arrow
		}
		else {
			if (event.keyCode == 37 || event.keyCode == 38) { offset.left = -1; offset.top = -1; } // left or up arrow
			else if (event.keyCode == 39 || event.keyCode == 40) { offset.left = 1; offset.top = 1; } // right or down arrow
		}

		if (event.shiftKey == true ) {
			offset.left *= 10;
			offset.top *= 10;
		}

		return offset;
	};

	this.warpDataToArray = function ( warpData ) {
		var warpDataArray = [];
		warpDataArray.push([warpData.warpPointLeftTop.left, warpData.warpPointLeftTop.top])
		warpDataArray.push([warpData.warpPointLeftBottom.left, warpData.warpPointLeftBottom.top])
		warpDataArray.push([warpData.warpPointRightTop.left, warpData.warpPointRightTop.top])
		warpDataArray.push([warpData.warpPointRightBottom.left, warpData.warpPointRightBottom.top])
		return warpDataArray;
	}

	this.getWarpData = function () {
		var warpData = {};

		warpData.warpPointLeftTop = this.getWarpPosition("warpPointLeftTop");
		warpData.warpPointLeftBottom = this.getWarpPosition("warpPointLeftBottom");
		warpData.warpPointRightTop = this.getWarpPosition("warpPointRightTop");
		warpData.warpPointRightBottom = this.getWarpPosition("warpPointRightBottom");

		return warpData;
	}

	this.getWarpPosition = function (element) {
		var warpPosition = {};

		warpPosition.left = parseFloat($('#' + element).css('left'));
		warpPosition.top = parseFloat($('#' + element).css('top'));

		return warpPosition;
	}

	this.setWarpDataCallback = function (_this, warpData) {

		_this.setWarpData(warpData);
	}

	this.setWarpData = function (warpData) {
		for (var element in warpData) {
			for (var style in warpData[element]) {
				$('#' + element).css(style, warpData[element][style]);
			}
		}
	}

	this.applyTransform = function (data) {
		applyTransform(this.warpTarget, this.warpDataToArray(this.warpDataOriginal), this.warpDataToArray(data));
	}

	this.getWarpDataWidth = function (warpData) {
		return warpData.warpPointRightBottom.left - warpData.warpPointLeftTop.left;
	}

	this.getWarpDataHeight = function (warpData) {
		return warpData.warpPointRightBottom.top - warpData.warpPointLeftTop.top;
	}
}

Warper.prototype.getRect = function () {
	var warpData = this.getWarpData();
	var rect = {};

	rect.x = warpData.warpPointLeftTop.left + this.radius;
	rect.y = warpData.warpPointLeftTop.top + this.radius;
	rect.width = (warpData.warpPointRightBottom.left - warpData.warpPointLeftTop.left);
	rect.height = (warpData.warpPointRightBottom.top - warpData.warpPointLeftTop.top);

	return rect;
}

Warper.prototype.init = function () {
	$("body").wrapInner("<div id='warp'></div>");
	this.warpTarget = $("#warp");
	this.warpTarget.css('transform', '');
	this.controlPoints = this.createControlPoints(this.warpTarget);
	this.warpDataOriginal = this.getWarpData();
	this.aspect = this.getWarpDataWidth(this.warpDataOriginal) / this.getWarpDataHeight(this.warpDataOriginal);
	this.loadWarpData('warping.json', this, this.setWarpDataCallback);

	document.addEventListener('keydown', this.warperKeyDownListener);
};

Warper.prototype.loadWarpData = function (fileName, _this, callback) {
	$.getJSON(fileName, function (warpData) {
		_this.loadedWarpData = warpData;
		callback(_this, warpData);
	});
};

Warper.prototype.saveWarpData = function (fileName, warpData) {
	var text = JSON.stringify( warpData );
    var pom = document.createElement('a');
    pom.setAttribute('href', 'data:text/json;charset=utf-8,' + encodeURIComponent(text));
    pom.setAttribute('download', fileName);
    pom.click();
}
  
Warper.prototype.createControlPoints = function (target) {
	var _i, _len, _ref, _results;
	var position;
	_ref = ['left top', 'left bottom', 'right top', 'right bottom'];
	_refName = ['LeftTop', 'LeftBottom', 'RightTop', 'RightBottom'];
	_results = [];
	for (_i = 0, _len = _ref.length; _i < _len; _i++) {
		position = _ref[_i];
		_results.push($('<div class="warppoint" id="warpPoint' + _refName[_i] + '">').css({
			border: this.radius + 'px solid red',
			borderRadius: this.radius + 'px',
			cursor: 'move',
			position: 'absolute',
			zIndex: 100000,
			visibility: 'hidden'
		}).appendTo('body').position({
			at: position,
			of: target,
			collision: 'none'
		}));
	}
	_results = ($(".warppoint"))
	return _results;
};

Warper.prototype.makeTransformable = function (selector, callback) {
	var that = this;
	return selector.each(function (i, element) {
		var p;
		$(that.controlPoints).draggable({
			start: (function (_this) {
				return function () {
					return $(element).css('pointer-events', 'none');
				};
			})(this),
			drag: (function (_this) {
				return function () {
					return applyTransform(element, that.warpDataToArray(that.warpDataOriginal), that.warpDataToArray(that.getWarpData()), callback);
				};
			})(this),
			stop: (function (_this) {
				return function () {
					applyTransform(element, that.warpDataToArray(that.warpDataOriginal), that.warpDataToArray(that.getWarpData()), callback);
					return $(element).css('pointer-events', 'auto');
				};
			})(this)
		});
		return element;
	});
};