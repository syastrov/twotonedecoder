#!/usr/bin/env python

################################
# Settings
################################

# Number of tones to measure sequentially before considering as a new tone group
NUM_TONES = 2

# Minimum difference between two tone frequencies in Hz to consider them as different tones
MIN_TONE_FREQUENCY_DIFFERENCE = 5.0

# Minimum length of time in seconds to consider a signal as a tone
MIN_TONE_LENGTH = 0.200

# Maximum standard deviation in tone frequency to consider a signal as one tone
MAX_TONE_FREQ_STD_DEVIATION = 10.0

# Loudness in dB, below which to ignore signals
SQUELCH = -70.

################################
# END Settings
################################

import sys
#sys.stdout = open("logfile.txt","w")

try:
  import numpy
except ImportError:
  print "NumPy required to perform calculations"
  raise

from PyQt4.QtCore import *
from PyQt4.QtGui import *

def schmitt(data, rate):
  loudness = numpy.sqrt(numpy.sum((data/32768.)**2)) / float(len(data))
  rms = 20.0 * numpy.log10(loudness)
  #print "RMS", rms
  if rms < SQUELCH:
    return -1

  blockSize = len(data) - 1

  #print blockSize
  freq = 0.
  trigfact = 0.6

  schmittBuffer = data
  
  A1 = max(schmittBuffer)
  A2 = min(schmittBuffer)

  #print "A1", A1, "A2", A2

  # calculate trigger values, rounding up
  t1 = round(A1 * trigfact)
  t2 = round(A2 * trigfact)

  #print "T1", t1, "T2", t2

  startpoint = -1
  endpoint = 0
  schmittTriggered = 0
  tc = 0
  schmitt = []
  for j in range(0, blockSize):
    schmitt.append(schmittTriggered)
    if not schmittTriggered:
      schmittTriggered = (schmittBuffer[j] >= t1)
    elif schmittBuffer[j] >= t2 and schmittBuffer[j+1] < t2:
      schmittTriggered = 0
      if startpoint == -1:
        tc = 0
        startpoint = j
        endpoint = startpoint+1
      else:
        endpoint = j
        tc += 1

  #print "Start, end", startpoint, endpoint
  #print "TC", tc
  if endpoint > startpoint:
    freq = rate * (tc / float(endpoint - startpoint))
    
  """
  from pylab import *
  ion()
  
  timeArray = arange(0, float(len(data)), 1)
  timeArray = timeArray / rate
  timeArray = timeArray * 1000  #scale to milliseconds

  hold(False)

  plot(timeArray, data, 'k', timeArray[startpoint:endpoint], [s*1000 for s in schmitt[startpoint:endpoint]], 'r')
  title('Frequency: %7.3f Hz' % freq)
  ylabel('Amplitude')
  xlabel('Time (ms)')

  draw()
  """

  return freq


class MeasurerThread(QThread):
  def __init__(self, parent = None):
    QThread.__init__(self, parent)
    self.running = True

  def __del__(self):
    self.running = False
    self.wait()
    
  def run(self):
    chunk = 2048
    
    if len(sys.argv) > 1:
      wavfile = sys.argv[1]
    else:
      wavfile = ''

    if not wavfile:
      try:
        import pyaudio
      except ImportError:
        print "PyAudio required to capture audio"
        raise
      
      pa = pyaudio.PyAudio()

      print "Device Info", pa.get_default_host_api_info()

      #input_device_index = pa.get_host_api_info_by_type(pyaudio.paOSS)['defaultInputDevice']
      input_device_index = pa.get_default_host_api_info()['defaultInputDevice']

      FORMAT = pyaudio.paInt16
      channels = 1
      rate = 44100
      
      stream = pa.open(format = FORMAT,
                      channels = channels,
                      rate = rate,
                      input = True,
                      input_device_index = input_device_index,
                      frames_per_buffer = chunk)

    else:
      import wave
      wav = wave.open(wavfile, 'r')
      rate = wav.getframerate()
      channels = wav.getnchannels()
      print "channels", wav.getnchannels()
      print "width", wav.getsampwidth()
      print "Wav rate", rate
    
    #for i in range(0, ATE / chunk * RECORD_SECONDS):
    freqBufferSize = int(MIN_TONE_LENGTH * rate / float(chunk))
    freqBuffer = numpy.zeros(freqBufferSize)
    freqIndex = 0
    lastFreq = 0.
    toneIndex = -1
    while self.running:
      if not wavfile:
        data = stream.read(chunk)
      else:
        data = wav.readframes(chunk)
        if wav.tell() >= wav.getnframes():
          break
      buf = numpy.fromstring(data, dtype=numpy.int16)
      if channels == 2:
        # Get rid of second channel
        buf = buf.reshape(-1, 2)
        buf = numpy.delete(buf, 1, axis=1)
        buf = buf.reshape(-1)

      #print "A", len(a)
      freq = schmitt(buf, rate)
      if freq > 0:
        print "Freq", freq
        freqBuffer[freqIndex % freqBufferSize] = freq
        freqIndex += 1
        print freqBuffer
        stddev = freqBuffer.std()
        print "Std deviation", stddev
        if stddev < MAX_TONE_FREQ_STD_DEVIATION:
          mean = freqBuffer.mean()
          # Clear ringbuffer
          #freqBuffer = numpy.zeros(freqBufferSize)
          print "Mean", mean, "Last", lastFreq
          if abs(mean - lastFreq) > MIN_TONE_FREQUENCY_DIFFERENCE:
            toneIndex = (toneIndex + 1) % NUM_TONES
            if toneIndex == 0:
              self.emit(SIGNAL("clearFrequencies()"))
            lastFreq = mean
            self.emit(SIGNAL("measureFrequency(float, int)"), mean, toneIndex)

    if not wavfile:
      stream.close()
      pa.terminate()
    else:
      wav.close()

class MainWindow(QWidget):
  def __init__(self, parent = None):
    QWidget.__init__(self, parent)
    
    self.thread = MeasurerThread()
    self.connect(self.thread, SIGNAL("measureFrequency(float, int)"), self.showFrequency)
    self.connect(self.thread, SIGNAL("clearFrequencies()"), self.clearFrequencies)
    self.thread.start()

    self.frequencyLCDs = []
    for i in range(NUM_TONES):
      self.frequencyLCDs.append(QLCDNumber())

    vbox = QVBoxLayout()
    for lcd in self.frequencyLCDs:
      lcd.setSegmentStyle(QLCDNumber.Flat)
      vbox.addWidget(lcd)

    self.clearFrequencies()

    self.setLayout(vbox)

    self.setWindowTitle(self.tr("Two-tone Decoder"))
    self.resize(200, 100)

  def showFrequency(self, freq, i):
    self.frequencyLCDs[i].display(freq)

  def clearFrequencies(self):
    for lcd in self.frequencyLCDs:
      lcd.display('')

if __name__ == "__main__":
  app = QApplication(sys.argv)
  window = MainWindow()
  window.show()
  sys.exit(app.exec_())