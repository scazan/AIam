var carrier; // this is the oscillator we will hear
var modulator; // this oscillator will modulate the amplitude of the carrier

setup();

function setup() {

    // createCanvas(window.innerWidth, window.innerHeight)
    // strokeWeight(3);
    // pg = createGraphics(window.innerWidth, window.innerHeight);
    // pg.colorMode(HSB, 360, 100, 100, 1)
    // colorMode(HSB,360,100,100,1);
    // pg.strokeWeight(0);

    carrier = new p5.Oscillator('sine');
    carrier.amp(.01); // set amplitude
    carrier.freq(220); // set frequency
    carrier.start(); // start oscillating

    modulator = new p5.Oscillator('square');
    modulator.disconnect();
    modulator.amp(.01); 
    modulator.freq(4); 
    modulator.start();

    carrier.freq( modulator.mult(100).add(44) );

}

