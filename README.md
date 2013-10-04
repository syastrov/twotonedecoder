twotonedecoder
=============

Decodes the frequencies of two-tone codes used in fire dispatch pager systems..
Calculates and displays the frequencies of the tones.

Cross-platform, free and open-source alternative to commercial software such as [ComTekk Two-tone Decoder](http://comtekk.us/two-tone-decoder.htm).

How to run on Ubuntu:
-----

Requires PyQt4, Numpy, and PyAudio.

On Ubuntu:

`sudo apt-get install python-numpy python-qt4 python-pyaudio`


To run:

`python twotonedecoder.py`

Screenshot
--------

![Screenshot](twotonedecoder.png)

How it works
--------

It uses a [Schmitt Trigger](http://en.wikipedia.org/wiki/Schmitt_trigger) to calculate each frequency.

It has a number of settings (shown with defaults):

 * NUM_TONES = 2
   * Number of tones to measure sequentially before considering as a new tone group

 * MIN_TONE_FREQUENCY_DIFFERENCE = 5.0
   * Minimum difference between two tone frequencies in Hz to consider them as different tones

 * MIN_TONE_LENGTH = 0.200
   * Minimum length of time in seconds to consider a signal as a tone

 * MAX_TONE_FREQ_STD_DEVIATION = 10.0
   * Maximum standard deviation in tone frequency to consider a signal as one tone

 * SQUELCH = -70.
   * Loudness in dB, below which to ignore signals


