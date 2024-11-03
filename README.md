
### Inspiration

My friends and I formed a band with drums, guitars, and lead singers, but we still need a keyboard player—that’s me! Every day, especially on weekends, I want to practice piano and make music. To do this, I have to take the school bus from my apartment to school, then walk a distance to transfer to the East and West Campus bus, which finally brings me to the Mary Biddle Music Building where there’s some piano rooms. Pianos like Steinways or Yamahas are all there! However, the commute takes about an hour, which is very inconvenient. I often wish I could practice piano at home.

There are two typical solutions to this problem: buying a car or getting a piano to keep at home. However, both are obviously very expensive. That’s where our product, Air Piano X, comes in as the perfect alternative!

### What it does

Air Piano X is a digital piano interface designed for ultimate portability. Using motion sensors and haptic feedback, Air Piano X allows users to play a virtual piano by simply positioning their hands as they would on a traditional keyboard. The system translates hand and finger movements into musical notes in real time, giving users an authentic piano-playing experience without a physical instrument. Compatible with a variety of devices, Air Piano X is ideal for practicing anywhere.

### How we built it

We started by researching and prototyping with a combination of motion-tracking technology and sound synthesis software. We programmed Air Piano X to accurately detect key presses and velocity. On the software side, we developed a responsive sound engine that uses a MIDI-based virtual piano to provide realistic feedback. We also incorporated haptic feedback for a more immersive experience, giving the user a sensation similar to pressing physical keys.

### Challenges we ran into

One of the biggest challenges was ensuring accuracy in tracking hand movements, especially given the complexity of piano techniques like dynamics and rapid note transitions. Balancing high accuracy, low latency, and portability was crucial but challenging, as we had to optimize both hardware and software to work seamlessly together.

### Accomplishments that we're proud of

We’re proud to have developed a functional prototype that delivers a realistic playing experience without the need for a physical piano. Achieving precise motion tracking and authentic sound synthesis was a major accomplishment, as was integrating haptic feedback to enhance user interaction. We’re excited by the positive feedback from early testers and how Air Piano X has the potential to change the way musicians practice and perform.

### What we learned

Throughout this project, we gained insights into the intricacies of motion tracking and sound synthesis. We learned the importance of refining user experience based on feedback, as well as the value of persistence in overcoming technical challenges. Developing Air Piano X also taught us a lot about balancing innovation with practical usability, especially when creating a product for musicians.

### What's next for Air Piano X

Our next steps include refining Air Piano X for improved accuracy and latency, as well as exploring new features like customizable sound libraries and cloud-based practice sessions for real-time collaboration with other musicians. We’re also looking into partnerships to scale up production and make Air Piano X accessible to a wider audience. Ultimately, we envision Air Piano X as a versatile tool for both beginners and professional musicians, enabling quality piano practice anywhere, anytime.

### Requirements

pip install -r requirements.txt

### Run the code

python air_pianox.py