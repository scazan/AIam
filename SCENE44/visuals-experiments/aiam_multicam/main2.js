
var SCREEN_WIDTH = window.innerWidth;
var SCREEN_HEIGHT = window.innerHeight;
var windowWidth = window.innerWidth;
var windowHeight = window.innerHeight;
var container, stats;

var camera, scene, renderer;

var mesh, texture, geometry, materials, material, current_material;

var light, pointLight, ambientLight,dirlight2;

var effect, resolution, numBlobs;

var effectController;

var time = 0;
var time2 = 0;

var clock = new THREE.Clock();

var cameras=[];
var helpers=[];

var row = 4
var col = 4
var numCameras=row*col;
var cube
var corner;
var gui = new dat.GUI();

var params = new function() {}

var warper = new Warper();
var multicam = true;
var guiVisible = false;
var listenToIncomingData = false;

var scale= 1000;
var oneBall;

var color = new THREE.Color();

init();
animate();
    
function init() {
	container = document.createElement('div');
    document.body.appendChild(container);

	// CAMERA

	camera = new THREE.PerspectiveCamera( 75, SCREEN_WIDTH / SCREEN_HEIGHT, 1, 10000 );
	camera.position.set( -500, 500, 1500 );

	// SCENE

	scene = new THREE.Scene();

	// LIGHTS

	light = new THREE.DirectionalLight( 0xffffff );
	light.position.set( 0.5, 0.5, 1 );
	scene.add( light );

	dirlight2 = new THREE.DirectionalLight( 0xffffff );
	dirlight2.position.set( 0.5, 0.5, 1 );
	scene.add( dirlight2 );
	

	pointLight = new THREE.PointLight( 0xff3300 );
	pointLight.position.set( 0, 0, 100 );
	scene.add( pointLight );

	ambientLight = new THREE.AmbientLight( 0xcccccc,.4 );
	scene.add( ambientLight );

	// MATERIALS

	current_material = new THREE.MeshPhongMaterial( { color: 0x000000, specular: 0x111111, shininess: 1, shading: THREE.FlatShading,side:THREE.DoubleSide } );

	// MARCHING CUBES

	resolution = 28;
	numBlobs = 10;

	effect = new THREE.MarchingCubes( resolution,current_material, true, true );
	effect.position.set( 0, 0, 0 );
	effect.scale.set(scale,scale,scale );

	effect.enableUvs = false;
	effect.enableColors = true;

	scene.add( effect );

	//helper
	// var geometry = new THREE.BoxGeometry(1600,1600,1600);
 //    var material = new THREE.MeshLambertMaterial({color: 0xc0c0c0,wireframe:true});
 //    cube = new THREE.Mesh(geometry, material);
 //    scene.add(cube)
	
	// var geometry = new THREE.BoxGeometry(40,40,40);
 //    var material = new THREE.MeshLambertMaterial({color: 0xffffff});
	// corner = new THREE.Mesh(geometry, material);
	// corner.position.set(0,-0,800)
 //    scene.add(corner)

	// RENDERER

	renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.setClearColor(0xdce2d6);
    container.appendChild(renderer.domElement);
	
	// GUI
	setupGui();
    gui.domElement.style.display = 'none'

    //CAMERAS
    var camerasFolder = gui.addFolder('cameras');
	
    for (var i = 0; i < row ; i++) {
         for (var j = 0 ; j < col; j++) {
            var index = j+i*col;
        
        	//cams:
            cameraN = new THREE.PerspectiveCamera( 40, window.innerWidth/window.innerHeight, .1, 100000 );
            cameraN.lookAt( scene.position );
            cameras.push(cameraN)
            cameraN.updateMatrixWorld();

            cameraN.up.set(Math.random(),Math.random(),Math.random())

            var f = camerasFolder.addFolder('cam'+index);

            camZ = String('cam'+index+'Z');
            params[camZ]= Math.random()+800;
            f.add(params,camZ,1,801);
            
            camX = String('cam'+index+'X');
            params[camX]= Math.random()*Math.PI*2;
            f.add(params,camX,0,Math.PI*2);
            
            camY = String('cam'+index+'Y');
            params[camY]= 0//random(index)*3 -1;
            f.add(params,camY,-1,2);
            
            camFov = String('cam'+index+'FOV');
            params[camFov]= random(index*345)*70 + 20;
            f.add(params,camFov,20,90);

        }
    }
	// //

	// renderer.gammaInput = true;
	// renderer.gammaOutput = true;

	// CONTROLS

	// controls = new THREE.OrbitControls( camera, renderer.domElement );

    setTimeout(function () { warper.init(); }, 100);

	var renderTargetParameters = { minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, format: THREE.RGBFormat, stencilBuffer: false };
	renderTarget = new THREE.WebGLRenderTarget( SCREEN_WIDTH, SCREEN_HEIGHT, renderTargetParameters );

	// EVENTS

	window.addEventListener( 'resize', onWindowResize, false );
    window.addEventListener('keydown', keyPressed, false);
}

function keyPressed(e){

    var key = event.keyCode ;
    console.log(key)
    switch (key) {

        case 65:    /*a*/
            if (multicam) {
            	multicam = false;
            } else {
				multicam = true;
            }
            break;

        case 83:    /*s gui*/ 
            if (guiVisible) {
            	guiVisible = false;
            	gui.domElement.style.display = 'none'
            } else {
				guiVisible = true;
				gui.domElement.style.display = 'block'
            }
            break;
        case 68:    /*d distort*/
        	if (warp) {
        		warp = false;
        		warper.applyTransform(warper.warpDataOriginal)
        	} else {
        		warp = true;
        		warper.applyTransform(warper.loadedWarpData)
        	}
            break;
         case 76: //L - listen to incoming data set
         	if (listenToIncomingData) {
        		listenToIncomingData = false;
        	} else {
        		listenToIncomingData = true;
        	}
    }
}
//

function onWindowResize( event ) {

	SCREEN_WIDTH = window.innerWidth;
	SCREEN_HEIGHT = window.innerHeight;

	camera.aspect = SCREEN_WIDTH / SCREEN_HEIGHT;
	camera.updateProjectionMatrix();

	renderer.setSize( SCREEN_WIDTH, SCREEN_HEIGHT );
	composer.setSize( SCREEN_WIDTH, SCREEN_HEIGHT );

	effectFXAA.uniforms[ 'resolution' ].value.set( 1 / SCREEN_WIDTH, 1 / SCREEN_HEIGHT );

}

function setupGui() {

	effectController = {

		speed: 0.15,
		numBlobs: 15,
		resolution: 22,
		isolation: 25,

		floor: false,
		wallx: false,
		wallz: false,

		matColor: "#ff7e7d",
		lightColor: "#f54242",
		backgroundColor: "#5f2b2b",
		bgColorSingle: "#ff2b2b",
		lx: -0.3,
		ly: -1,
		lz: -.5,
		distort:true
	};

	gui.remember(effectController);
	var h, m_h, m_s, m_l, matColor,lightColor,backgroundColor,bgColorSingle,distort;

	h = gui.add(effectController,"distort")
	
	h = gui.addFolder( "Colors" );
	// Colors

	matColor = h.addColor( effectController, "matColor").listen();
	lightColor = h.addColor( effectController, "lightColor");
	backgroundColor = h.addColor( effectController, "backgroundColor");
	bgColorSingle = h.addColor( effectController, "bgColorSingle");
	
	// light (directional)

	h = gui.addFolder( "Directional light orientation" );

	h.add( effectController, "lx", -1.0, 1.0, 0.025 ).name("x");
	h.add( effectController, "ly", -1.0, 1.0, 0.025 ).name("y");
	h.add( effectController, "lz", -1.0, 1.0, 0.025 ).name("z");

	// simulation

	h = gui.addFolder( "Simulation" );

	h.add( effectController, "speed", 0, 1.0, 0.05 ).listen();
	h.add( effectController, "numBlobs", 1, 50, 1 ).listen();
	h.add( effectController, "resolution", 14, 100, 1 );
	h.add( effectController, "isolation", 10, 300, 1 ).listen();

	h.add( effectController, "floor" );
	h.add( effectController, "wallx" );
	h.add( effectController, "wallz" );
}

// this controls content of marching cubes voxel field

function updateCubes( object, time, numblobs, floor, wallx, wallz ) {

	object.reset();

	// fill the field with some metaballs

	var i, ballx, bally, ballz, subtract, strength;

	subtract = 12;
	strength = 1.2 / ( ( Math.sqrt( numblobs ) - 1 ) / 4 + 1 );

	for ( i = 0; i < numblobs; i ++ ) {

		ballx = Math.sin( i + 1.26 * time * ( 1.03 + 0.5 * Math.cos( 0.21 * i ) ) ) * 0.24 + 0.5;
		bally = Math.abs( Math.cos( i + 1.12 * time * Math.cos( 1.22 + 0.1424 * i ) ) ) * 0.77; // dip into the floor
		ballz = Math.cos( i + 1.32 * time * 0.1 * Math.sin( ( 0.92 + 0.53 * i ) ) ) * 0.24 + 0.5;

		object.addBall(ballx, bally, ballz, strength, subtract);
		if (i==0) {
			var radius = scale * Math.sqrt( strength / subtract )
		}
	}

	if ( floor ) object.addPlaneY( 2, 12 );
	if ( wallz ) object.addPlaneZ( 2, 12 );
	if ( wallx ) object.addPlaneX( 2, 12 );

}

//
function random(seed) {
    var x = Math.sin(seed) * 10000;
    return x - Math.floor(x);
}


function animate() {

	requestAnimationFrame( animate );
	render();
}

function render() {

	if (listenToIncomingData) {
		effectController.isolation = Math.floor(incomingData*90)+10;
		effectController.speed = incomingData/4 + .05;
		effectController.numblobs = Math.floor(incomingData*8)+2;
		// color.set(effectController.matColor)
		// color.offsetHSL(0,incomingData,0);
	} 

	var delta = clock.getDelta();
	time += delta * effectController.speed;
	time2 += delta*.5;

	if (multicam) {
		for (var i = 0; i < row ; i++) {
			for (var j = 0 ; j < col; j++) {
			    var index = j+i*col;
			    var rot = params[String('cam'+index+"X")] + time2/4
			    var y = params[String('cam'+index+'Y')]
			    var r = params[String('cam'+index+"Z")]

			    var cam = cameras[index]
			    var left   = Math.floor( windowWidth  * 1/col * i );
			    var bottom = Math.floor( windowHeight * 1/col * j+1 );
			    var width  = Math.floor( windowWidth  * 1/col );
			    var height = Math.floor( windowHeight * 1/col );
			    renderer.setViewport( left, bottom, width, height );
			    renderer.setScissor( left, bottom, width, height );
			    renderer.setScissorTest( true );

			    camera.aspect = width / height;
			    
			    renderer.setClearColor(effectController.backgroundColor)// new THREE.Color().setHSL( 0.004, 1, .5 ) );

			    renderer.render( scene, cam);

			    cameras[index].position.set(r*Math.cos(rot),0, r*Math.sin(rot));
			    cameras[index].lookAt( new THREE.Vector3( scene.position.x,scene.position.y+y,scene.position.z) );

			    cameras[index].fov = params[String('cam'+index+"FOV")]

			    cameras[index].updateProjectionMatrix();

	    // helpers[index].position.copy(cameras[index].position)
	    // helpers[index].lookAt(scene.position)
			}
		}

	} else {
		//single cam view 
		camera.aspect = SCREEN_WIDTH / SCREEN_HEIGHT;
		renderer.setViewport( 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT );
		renderer.setScissor( 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT );
		renderer.setScissorTest( true );
		renderer.setClearColor(effectController.bgColorSingle)// new THREE.Color().setHSL( 0.004, 1, .5 ) );
		camera.lookAt(effect.position)
		// console.log(oneBall)
		
		renderer.render( scene, camera );

	}
	// marching cubes

	if ( effectController.resolution !== resolution ) {

		resolution = effectController.resolution;
		effect.init(Math.floor( resolution ));
	}

	if ( effectController.isolation !== effect.isolation ) {

		effect.isolation = effectController.isolation;
	}

	updateCubes( effect, time, effectController.numBlobs, effectController.floor, effectController.wallx, effectController.wallz );



	// materials

	effect.material.color.set( effectController.matColor)//hue, effectController.saturation, effectController.lightness );

	// lights

	light.position.set( effectController.lx, effectController.ly, effectController.lz );
	light.position.normalize();
	dirlight2.position.set(light.position.x*-1,light.position.y*-1+.5,light.position.z)
	pointLight.color.set( effectController.lightColor);

	// render


	// renderer.clear();
	// renderer.render( scene, camera );
}

