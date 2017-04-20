s.waitForBoot({
	var startReceiver = {
		var lastX = 0,
			lastY = 0,
			lastZ = 0,
			maxY = 0,
			maxX = 0,
			window;

		var addEnergy = { | mag |
			var newEnergy = (~energyX + mag);

			if(newEnergy >= 1, {
				~energyX = 1;
			}, {
				~energyX = newEnergy;
			});
		};

		~energyX = 0;
		~voiceFreqBus = Bus.control(s,1);
		~voiceAmpBus = Bus.control(s,1);
		~voiceAmpBus.set(1);

		Tdef(\gravity, {
			{
				if(~energyX > 0.01, {
					~energyX = ~energyX - 0.00027;
					~voiceFreqBus.set(~energyX**1.15);
					~voiceAmpBus.set(~energyX**2);
				}, {
					~voiceFreqBus.set(0);
					~voiceAmpBus.set(0);
				});

				0.001.wait;
			}.loop;
		}).play;


		OSCdef(\tracker, { | msg |
			var x = msg[2].asFloat / 1800,
				y = msg[3].asFloat / 500,
				z = msg[4].asFloat / 7000;

			var diffX = 0,
				diffY = 0,
				diffZ = 0;

			diffX = (lastX - x).abs;
			diffY = (lastY - y).abs;
			diffZ = (lastZ - z).abs;

			addEnergy.value(diffX);
			z = (z-0.5).abs / (1-0.5);

			if(diffX > 0.045, {
				~synth.set(\vowel, [1,2,3,4,5].choose);
				~synth2.set(\vowel, [1,2,3,4,5].choose);
			});

			#lastX, lastY, lastZ = [x, y, z];

		}, path: \center, recvPort: 15002);

	~synth = Synth(\voice, [\voiceFreqBus, ~voiceFreqBus, \voiceAmpBus, ~voiceAmpBus]);

	u = Pbind(
		\type, \set,
		\id, ~synth.nodeID,
		\args, #[\vowel],
		\dur, 4.5,
		\vowel, Prand([0,1,2,3,4], inf),
	).play;

	~synth2 = Synth(\voice, [\voiceFreqBus, ~voiceFreqBus, \voiceAmpBus, ~voiceAmpBus]);

		h = Pbind(
			\type, \set,
			\id, ~synth2.nodeID,
			\args, #[\vowel, \transpose],
			\transpose, 0.05,
			\dur, 4.5,
			\vowel, Prand([0,1,2,3,4], inf),
		).play;

		window = Window.new("AIam Sound", Rect(100, 100, 100, 100)).front;
		window.view.background_(Color.new255(153, 255, 102));

		window.drawFunc = Routine({
			{
				window.view.background_(Color.new255(~energyX * 255, 0, 102));
				0.yield;
			}.loop;
		});

		{ while { window.isClosed.not } { window.refresh; 0.04.wait; } }.fork(AppClock);
	};

	SynthDef(\voice, { arg
		freq = 620,
		amp = 0.5,
		vibratoSpeed = 0,
		vibratoDepth = 4,
		vowel = 0,
		att = 0.01,
		rel = 0.1,
		lag = 1,
		gate = 1,
		hasFreq = 0,
		transpose = 0.5,
		pitchLag=0.00001,
		voiceFreqBus,
		voiceAmpBus;

		var in, vibrato, env, va, ve, vi, vo, vu, snd;

		freq = In.kr(voiceFreqBus).squared * 600 + 60;
		//# freq, hasFreq = Pitch.kr(SoundIn.ar(0) * 200);
		freq = Lag.kr(freq*transpose,pitchLag);
		vibrato = SinOsc.kr(vibratoSpeed, mul: vibratoDepth);
		in = Saw.ar(Lag.kr(freq, lag) + vibrato);
		env = EnvGen.kr(Env.asr(att, 1, rel), gate, doneAction: 2);

		va = BBandPass.ar(
			in: in,
			freq: [ 600, 1040, 2250, 2450, 2750 ],
			bw: [ 0.1, 0.067307692307692, 0.048888888888889, 0.048979591836735, 0.047272727272727 ],
			mul: [ 1, 0.44668359215096, 0.35481338923358, 0.35481338923358, 0.1 ]);

		ve = BBandPass.ar(
			in: in,
			freq: [ 400, 1620, 2400, 2800, 3100 ] ,
			bw: [ 0.1, 0.049382716049383, 0.041666666666667, 0.042857142857143, 0.038709677419355 ],
			mul: [ 1, 0.25118864315096, 0.35481338923358, 0.25118864315096, 0.12589254117942 ]);

		vi = BBandPass.ar(
			in: in,
			freq: [ 250, 1750, 2600, 3050, 3340 ] ,
			bw: [ 0.24, 0.051428571428571, 0.038461538461538, 0.039344262295082, 0.035928143712575 ],
			mul: [ 1, 0.031622776601684, 0.15848931924611, 0.079432823472428, 0.03981071705535 ] );

		vo = BBandPass.ar(
			in: in,
			freq:[ 400, 750, 2400, 2600, 2900 ] ,
			bw: [ 0.1, 0.10666666666667, 0.041666666666667, 0.046153846153846, 0.041379310344828 ],
			mul: [ 1, 0.28183829312645, 0.089125093813375, 0.1, 0.01 ]);

		vu = BBandPass.ar(
			in: in,
			freq: [ 350, 600, 2400, 2675, 2950 ],
			bw: [ 0.11428571428571, 0.13333333333333, 0.041666666666667, 0.044859813084112, 0.040677966101695 ],
			mul: [ 1, 0.1, 0.025118864315096, 0.03981071705535, 0.015848931924611 ]);

		snd = SelectX.ar(Lag.kr(vowel, lag), [va, ve, vi, vo, vu]);
		snd = snd.flatten(2);
		snd = snd * (Lag.kr(In.kr(voiceAmpBus), 0.001) * 0.25);

		Out.ar(0, ([ snd, snd] * env * (amp.tanh * 6)).tanh );
	}).add;


	AppClock.sched(5, startReceiver);
});



