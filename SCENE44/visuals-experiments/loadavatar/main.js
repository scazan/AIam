var renderer,scene,camera;
var mirrorCamera;
var texture, floortex;
var obj;
var count = 0;

var dirCode = [38,39,40,37];
var keys = []; 
var radius = 2;
var cubesPhy = [];
var cubes=[];
var mirrorCameras=[];
var light;
var avatar;
var c;
var mixer;
var clock = new THREE.Clock();

var character;

var floor;
var skeletonHelper;
var mixer;
var bones;
 var quaternion;
var websocket

var Hips
var RightUpLeg 
var RightLeg
var RightFoot


// pose_
// [29460, 'Hips', -0.1586342751979828, 0.2167617231607437, 2.474078893661499]
// [29460, 'RightUpLeg', -0.6808388233184814, 0.21935366094112396, -0.12414476275444031]
// [29460, 'RightLeg', 0.9893349409103394, -0.16190074384212494, -0.4553258419036865]
// [29460, 'RightFoot', -0.11761488765478134, -0.13382431864738464, 0.10655833035707474]
// [29460, 'LeftUpLeg', -0.7044620513916016, 0.10775775462388992, 0.008671646006405354]
// [29460, 'LeftLeg', 0.9057791829109192, 0.16874495148658752, 0.11122091859579086]
// [29460, 'LeftFoot', -0.08927509188652039, -0.0612177737057209, 0.3628622591495514]
// [29460, 'Spine', 0.0870179608464241, -0.0035606552846729755, -0.03427036851644516]
// [29460, 'Spine1', 0.02247171476483345, -0.0005825746338814497, -0.0074785128235816956]
// [29460, 'Spine2', 0.03382568433880806, -0.0009605548111721873, -0.011582626961171627]
// [29460, 'Spine3', -0.010978000238537788, -0.0018891791114583611, -0.014047365635633469]
// [29460, 'Neck', -0.007833323441445827, -0.006698347628116608, -0.028779862448573112]
// [29460, 'Head', -0.22056438028812408, -0.015026949346065521, -0.24432362616062164]
// [29460, 'RightShoulder', 0.22137117385864258, 0.03976397588849068, 0.20161192119121552]
// [29460, 'RightArm', -0.4341822564601898, -0.5516433715820312, 0.09723659604787827]
// [29460, 'RightForeArm', -0.9676337242126465, -0.34729740023612976, 0.14676259458065033]
// [29460, 'RightHand', -0.07646813988685608, -0.002602894324809313, -0.05737009271979332]
// [29460, 'RightHandThumb1', 0.21174800395965576, -0.4825597405433655, 0.4338180720806122]
// [29460, 'RightHandThumb2', -8.778960669530989e-09, 1.1809860644973469e-08, -0.17453283071517944]
// [29460, 'RightHandThumb3', -2.8715738675799685e-09, 1.2823647921322845e-08, -0.17453284561634064]
// [29460, 'RightInHandIndex', 1.54256944995268e-08, -2.0916759435607446e-09, 1.3929008169100143e-08]
// [29460, 'RightHandIndex1', 0.016192050650715828, -0.34870532155036926, 0.047357942909002304]
// [29460, 'RightHandIndex2', 2.320556191648393e-08, -0.418878972530365, -8.370777493382775e-08]
// [29460, 'RightHandIndex3', -8.675876017605333e-09, -0.34906575083732605, -5.894852250776239e-08]
// [29460, 'RightInHandMiddle', 4.406957909708353e-09, 1.9801982276135277e-09, -2.127081011327192e-10]
// [29460, 'RightHandMiddle1', -3.123906022750589e-09, -0.3490656614303589, -5.384217161008564e-08]
// [29460, 'RightHandMiddle2', -1.1756293716302935e-09, -0.41887885332107544, -6.64470860556321e-08]
// [29460, 'RightHandMiddle3', -6.269737617969895e-09, -0.3490656912326813, -5.024725169278099e-08]
// [29460, 'RightInHandRing', 2.211667649021365e-08, -5.52457080083002e-10, -8.1300495224923e-09]
// [29460, 'RightHandRing1', -0.01904641091823578, -0.34856700897216797, -0.05571353808045387]
// [29460, 'RightHandRing2', -1.0424456853286301e-08, -0.4188789427280426, -8.242645321843156e-08]
// [29460, 'RightHandRing3', -6.936939467294678e-09, -0.34906572103500366, -5.74738585612522e-08]
// [29460, 'RightInHandPinky', 4.360478556009184e-08, -6.9376642208851536e-09, 1.2648976976947779e-08]
// [29460, 'RightHandPinky1', -0.05581258237361908, -0.34475526213645935, -0.16383224725723267]
// [29460, 'RightHandPinky2', 4.109024231979674e-09, -0.41887885332107544, -7.810423596765759e-08]
// [29460, 'RightHandPinky3', 5.703444383442502e-09, -0.3490656316280365, -6.36899315509254e-08]
// [29460, 'LeftShoulder', 0.06123911589384079, -0.24821466207504272, -0.03590630367398262]
// [29460, 'LeftArm', -0.9320741295814514, 0.7272706031799316, 0.6138334274291992]
// [29460, 'LeftForeArm', -0.37154966592788696, 0.9084221720695496, -0.5434913039207458]
// [29460, 'LeftHand', -0.07740812003612518, 0.11988826841115952, -0.052754826843738556]
// [29460, 'LeftHandThumb1', 0.21174800395965576, 0.4825597405433655, -0.4338180720806122]
// [29460, 'LeftHandThumb2', -9.054362593019505e-09, -1.2636672153121253e-08, 0.17453283071517944]
// [29460, 'LeftHandThumb3', -2.843641766503424e-09, -6.665707985575864e-09, 0.17453286051750183]
// [29460, 'LeftInHandIndex', 9.357464136883209e-09, 4.650846818776699e-09, -1.3718220337466391e-08]
// [29460, 'LeftHandIndex1', 0.01619204878807068, 0.34870532155036926, -0.0473579540848732]
// [29460, 'LeftHandIndex2', 4.098575256961112e-09, 0.418878972530365, 8.789597671921001e-08]
// [29460, 'LeftHandIndex3', -6.076626313245015e-09, 0.34906578063964844, 5.504334410488809e-08]
// [29460, 'LeftInHandMiddle', -4.1263858996387626e-09, 1.014062833704088e-09, 5.773944433684619e-09]
// [29460, 'LeftHandMiddle1', -6.409261565920588e-09, 0.3490656614303589, 5.949204151534104e-08]
// [29460, 'LeftHandMiddle2', -9.580438664613666e-10, 0.41887885332107544, 6.326265378220342e-08]
// [29460, 'LeftHandMiddle3', 1.952741746080733e-09, 0.3490656912326813, 5.234606348381021e-08]
// [29460, 'LeftInHandRing', 1.1042086356383152e-08, 2.3467339183014246e-09, 1.2261902604393526e-08]
// [29460, 'LeftHandRing1', -0.019046418368816376, 0.34856700897216797, 0.05571354553103447]
// [29460, 'LeftHandRing2', 1.0859909638227805e-09, 0.4188789427280426, 8.653796612634324e-08]
// [29460, 'LeftHandRing3', -2.362427586888316e-09, 0.34906575083732605, 5.4576105412706966e-08]
// [29460, 'LeftInHandPinky', 3.9910773352858087e-08, 9.18318932008333e-09, -7.72664510151344e-09]
// [29460, 'LeftHandPinky1', -0.05581258609890938, 0.34475526213645935, 0.16383224725723267]
// [29460, 'LeftHandPinky2', 8.660347106115296e-09, 0.41887885332107544, 6.331562474315433e-08]
// [29460, 'LeftHandPinky3', 6.316054790289627e-09, 0.3490656316280365, 6.146390774119936e-08]

  var data=1;

  // When the connection is open, send some data to the server
  websocket.onopen = function () {
    console.log('websocket_ready')
  };

  // Log errors
  websocket.onerror = function (error) {
    console.log(error);
  };

  // Log messages from the server
  websocket.onmessage = function (e) {
    // console.log(e.data);

    data = JSON.parse(e.data)
    
    if (bones[data[0]] !== undefined) {
      if (data[0] != "Hips") {

  

// -0.6717374920845032,-0.4149509370326996,0.17982159554958344

//       'LeftUpLeg', -0.14602670073509216, -0.20963644981384277, 0.018955092877149582]
// [13434, 'LeftLeg', 0.20726293325424194, 0.09113911539316177, -0.19361883401870728]
// [13434, 'LeftFoot', 0.12960588932037354, 0.056863319128751755, 0.07861680537462234]
      // if  (data[0] == "RightUpLeg") {
      //     // console.log( bones[data[0]].rotation );
      //     // [17159, 'LeftUpLeg', -0.5052275061607361, -0.1597336232662201, 0.07590659707784653]

      //     bones["RightUpLeg"].rotation.set(data[1],data[2],data[3], 'XYZ' )
      // }
      // if  (data[0] == "RightLeg") {
      //     // console.log( bones[data[0]].rotation );
      //     bones["RightLeg"].rotation.set(data[3],data[1],data[2], 'XYZ' )
      // }
     
      // if  (data[0] == "RightFoot") {
      //     // console.log( bones[data[0]].rotation );
      //     bones["RightFoot"].rotation.set(data[3],data[1],data[2], 'XYZ' )
      // }
      // if  (data[0] == "Hips") {
      //     // console.log( bones[data[0]].rotation );
      //     bones["Hips"].rotation.set(data[1],data[2],data[3], 'XYZ' )
      // }
       // bones[data[0]].rotation.set(data[1],data[2],data[3], 'XYZ' )
    }
    }
  };

  sendSocketMsg = function(msg){
    if(websocket.readyState == 1){
        websocket.send(msg);
      }
    else{
      websocket.onopen = function(e){
        websocket.send(msg);
      }
    }
  }


document.addEventListener('keydown', function(e) {
   keys[e.keyCode] = true;
}, false);

document.addEventListener('keyup', function(e) {
   keys[e.keyCode] = false;
}, false);

var textureLoader = new THREE.TextureLoader();
// var loader = new THREE.ColladaLoader();

// loader.options.convertUpAxis = true;
// loader.options.centerGeometry = true;
var loader = new THREE.JSONLoader();

textureLoader.load( 'grayDome2KK.jpg', function ( t ) {
  texture = t;

  // loader.load('avatar2.dae', function(collada) {
  //   console.log(collada.scene)
  //   //blocky.dae - avatar name
  //   //avatar.dae - "human1_002_001"
  //   c = collada.scene.getObjectByName( "avatar_export", true );
  //   // console.log(collada)

  //   var colladaObject=c.children[0];
  //   avatar = colladaObject;
  //   c.position.y = 0;
  //   c.scale.set(.01,.010,.0100);
  //   c.updateMatrix();
  //   skeletonHelper = new THREE.SkeletonHelper(c);
  //   avatar.bind( avatar.skeleton );
    loader.load('avatar.json', function (geometry, materials) {
    var material = new THREE.MultiMaterial( materials );
    character = new THREE.SkinnedMesh(
      geometry,
      material
    );
    init();
  })
  

  
});

function init(){
  websocket = new WebSocket("ws://localhost:8888/ws");

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setClearColor(0x000000);
  renderer.setSize(window.innerWidth, window.innerHeight)
  renderer.setPixelRatio( window.devicePixelRatio );
  
  // renderer.shadowMap.enabled = true;
  // renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  
  document.body.appendChild(renderer.domElement);

  scene = new THREE.Scene();
  // scene.fog = new THREE.FogExp2(0xffffff, .02);


    scene.add(character);

  //env
  // scene.add(skeletonHelper)
  // skeletonHelper.update();



  var mat = new THREE.MeshPhongMaterial( { color: 0x2194CE, specular: 0x111111, shininess: 30, shading: THREE.SmoothShading,skinning:true,side:THREE.DoubleSide } ) 
  // // avatar.material = mat
  // var b = avatar.skeleton.bones
  // bones = {};

  // for (var i = 0, l = b.length; i < l; i++) {
  //     bones[b[i].name] = b[i];
  // }
  // bones["Hips"].rotation.set( -Math.PI/2,0,0);



  // cornellBox.recieveShadow = true;
  // cornellBox.castShadow = true;
  // var size = 1.5;
  // var sphereGeometry = new THREE.SphereGeometry(size,32,32);

  camera = new THREE.PerspectiveCamera( 90, window.innerWidth/window.innerHeight, .1, 2000 );

  camera.position.set(0,1.2,2.5 )
  // camera.rotation.set(0,-Math.PI/2,0)

  // mirrorCamera = new THREE.CubeCamera( 0.1, 5000, 128 );
  // mirrorCamera.renderTarget.texture.minFilter = THREE.LinearMipMapLinearFilter;

  // scene.add( mirrorCamera );
 
  var geometry = new THREE.SphereGeometry( 100, 32,32 );
  var mat = new THREE.MeshBasicMaterial( { fog:true, map:texture});

  obj = new THREE.Mesh(geometry, mat);

  obj.scale.x = -1
  scene.add(obj);

  var geometry = new THREE.SphereGeometry( .1, 16,16 );
  var mat = new THREE.MeshBasicMaterial( { color:0xff00000});
  Hips = new THREE.Mesh(geometry, mat);
    Hips.position.set(0,0,0)
  RightUpLeg = new THREE.Mesh(geometry, mat);
    RightUpLeg.position.set(0,-.5,0)
  RightLeg = new THREE.Mesh(geometry, mat);
    RightLeg.position.set(0,-.5,0)
  RightFoot =new THREE.Mesh(geometry, mat);
    RightFoot.position.set(0,-.5,0)

   RightLeg.add(RightFoot)
   RightUpLeg.add(RightLeg)
   Hips.add(RightUpLeg)
   scene.add(Hips) 
   

  var ambient = new THREE.AmbientLight( 0xffffff );
  scene.add( ambient );

//Light todo
  light = new THREE.SpotLight( 0xffffff,.1 );
  light.target.position.set( 0, 0, 0);
  light.position.set(7.5,15,0)
  scene.add( light );

  var lights = [];

  lights[ 0 ] = new THREE.PointLight( 0xffffff, 1, 0 );
  lights[ 1 ] = new THREE.PointLight( 0xffffff, 1, 0 );
  lights[ 2 ] = new THREE.PointLight( 0xffffff, 1, 0 );

  lights[ 0 ].position.set( 0, 3, 0 );
  lights[ 1 ].position.set( 1, 2, 1 );
  lights[ 2 ].position.set( - 1, - 2, - 1 );

  scene.add( lights[ 0 ] );
  scene.add( lights[ 1 ] );
  scene.add( lights[ 2 ] );

  var sphereSize = 1;
  var pointLightHelper = new THREE.PointLightHelper( lights[ 1 ], sphereSize );
  scene.add( pointLightHelper );

  // PLANE
  var floorMaterial = new THREE.MeshBasicMaterial( {color:0x779ECB,side:THREE.DoubleSide } );
  var floorGeometry = new THREE.PlaneGeometry(5, 5, 1, 1);
  var floor = new THREE.Mesh(floorGeometry, floorMaterial);
  floor.rotation.set(Math.PI/2,0,0)
  floor.position.x = 0;
  scene.add( floor );

  controls = new THREE.OrbitControls(camera, renderer.domElement);
  
  animate();
  
  window.addEventListener('resize', onWindowResize, false);
  window.addEventListener("keydown",key,false)
}

function key(e){
  var comb = ['XYZ','XZY','YXZ','YZX','ZXY','ZYX']
  var rand = comb[Math.floor(Math.random() * comb.length)];
  var pos =[-0.4149509370326996, 0.17982159554958344, -0.6717374920845032]

  shuffle(pos)
  bones["RightUpLeg"].rotation.set( pos[0],pos[1],pos[2], rand )
  console.log(pos)
  console.log(rand)
}

function shuffle(a) {
    for (let i = a.length; i; i--) {
        let j = Math.floor(Math.random() * i);
        [a[i - 1], a[j]] = [a[j], a[i - 1]];
    }
}

var dt = 1/60;

function animate() {
    var time = performance.now() * 0.0001;
    var delta = clock.getDelta();

    // [29472, 'LeftArm', 0.5386573076248169, 0.7956953048706055, -0.7388981580734253]


    // if( mixer ) mixer.update( clock.getDelta() );

    // if (data != 1) {

    //   // for ( var i = 0; i < avatar.skeleton.bones.length; i ++ ) {

    //   //   avatar.skeleton.bones[ i ].position.y = data

    //   // }
    //   avatar.skeleton.bones[ data[0] ].position.y = data[1];
    //   avatar.skeleton.bones[ data[0] ].position.x = data[2];
    // }
    // console.log( bones[data[0]] );

   

    // quaternion = new THREE.Quaternion();
    // quaternion.setFromEuler(a);
    // var bonerot = bones["LeftArm"].rotation.toVector3();
    // //bones["LeftArm"].rotation.set(0,Math.sin( time ) * 26,Math.sin( -time ) * 2 ) 
    // bonerot.applyQuaternion(quaternion)
    // bones["LeftArm"].rotation.set(0.5386573076248169, 0.7956953048706055, -0.7388981580734253, 'XYZ' )
    // console.log(data)
    // if (data != 1) {
    //   bones["Hips"].position.z = data[1]/10;
    //   bones["Hips"].position.x = data[0]/10;
    // }
    
    // skeletonHelper.update()

   
    requestAnimationFrame(animate);
    renderer.render(scene, camera);

}

function onWindowResize() {
    camera.left = window.innerWidth / - 2;
    camera.right = window.innerWidth / 2;
    camera.top = window.innerHeight / 2;
    camera.bottom = window.innerHeight / - 2;
    camera.updateProjectionMatrix();
    renderer.setSize( window.innerWidth, window.innerHeight );
}
