var warper = new Warper();
warper.warping=true;
var contianer, renderer, camera, scene;

init()

	
function init() {
    setTimeout(function () { warper.init(); }, 100);
    
    container = document.createElement('div');
    document.body.appendChild(container);

    scene = new THREE.Scene();
	camera = new THREE.PerspectiveCamera( 40, window.innerWidth/window.innerHeight, .1, 10000 );
    camera.position.set(0,0,13);


    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.setClearColor(0xdce2d6);
    container.appendChild(renderer.domElement);


}