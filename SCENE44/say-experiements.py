import os
import random
import time

# words = ["I am sorry","I don't know","I understand your pain", "I feel your pain","That must be tough for you","I am happy for you","That's wonderful!","You're amazing","How can I help you?","I don't care.","Actually it is your fault.","Just let it go","Don't pay attention to them"]
# words = ["just let it go!"]
# steps = ["left hand to high front", "right hip to middle right", "left foot to low left front", "chest to middle front", "right elbow to middle back","left knee to middle left back","left foot to low right","head to low center","left elbow to middle right", "right shoulder to high right","chest to middle back","STOP","left hip to middle left back","right elbow to high left forward","head to low left","right foot to high center","chest to high center","right foot to low back"]

bodyparts = ["left foot","right foot","left knee","right knee", "right hip","left hip","chest","head","right shoulder","left shoulder","right elbow","left elbow","left hand","right hand"]
directions = ["up","down","forward","back","right","left"]
orientations = ["high","low","middle"," "]

t = 5; #seconds
steps = 400 

# t= 0;
# rnd = random.randint(0, len(words)-1);

os.system("say ready")
time.sleep(1)

for x in xrange(0,steps):
# 	randomword = words[random.randint(0, len(words)-1)].encode('string-escape')
	randomBodypart = bodyparts[ random.randint(0, len(bodyparts)-1)].encode('string-escape')
	randomDirection = directions[random.randint(0, len(directions)-1)].encode('string-escape')
	randomOrientation = orientations[random.randint(0, len(orientations)-1)].encode('string-escape')
	
	os.system("say "+randomBodypart + " " + randomOrientation + " " + randomDirection)
	time.sleep(t)

# 	# os.system("say "+randomword)
# 	print(x)
	# t -= .055

# for x in xrange(0,len(steps)-1):
# 	randomword = steps[random.randint(0, len(steps)-1)].encode('string-escape')
# 	os.system("say "+steps[x])
# 	print(x)
	# time.sleep(t)


os.system("say congratulations")
