import ROOT
import rootUtils as ut
from array import array
import os
import numpy as np

ROOT.gSystem.Load("libpythia8")

# this C++ code is needed to avoid segmentation violation
# when accessing pythia.generator.info in PyROOT+Pythia8(since at least v8.309)
# This issue is likely due to broken python binding of Pythia's infoPython() method.
ROOT.gInterpreter.Declare('''
const Pythia8::Info& generator_info(Pythia8::Pythia& pythia) {
    return pythia.info;
}
''')

nudict = {12: "nue", -12: "anue", 14: "numu", -14: "anumu", 16: "nutau", -16: "anutau"}

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-f", "--nuflavour",  action='append', type=int, dest='nu_flavour', help="neutrino flavour", default=None)
parser.add_argument("-b", "--heartbeat",  dest="heartbeat", type=int,  help="progress report", default=10000)
parser.add_argument("-n", "--pot",  dest="Np", type=int,  help="proton collisions", default=1000000)
parser.add_argument("--firstEvent",  dest="firstEvent", type=int,  help="firstEvent", default=0)
parser.add_argument("-Ecm", "--energyCM",  dest="eCM", type=float,  help="center of mass energy [GeV]", default=13600.)
parser.add_argument('-C', '--charm', action='store_true', dest='charm',help="ccbar production", default=False)
parser.add_argument('-B', '--beauty', action='store_true', dest='beauty',help="bbbar production", default=False)
parser.add_argument('-H', '--hard', action='store_true', dest='hard',help="all hard processes", default=False)
parser.add_argument('-W', '--weak', action='store_true', dest='weak',help="weak boson production", default=False)
parser.add_argument('-X', '--PDFpSet',dest="PDFpSet",  type=str,  help="PDF pSet to use", default="13")
parser.add_argument('-m', "--unstablemesons", dest="unstablemesons",  action='store_true',  help="make light mesons unstable", default=False)
parser.add_argument('-EtaMin',dest="eta_min",  type=float,  help="minimum eta for neutrino to pass", default=6.)
parser.add_argument('-EtaMax',dest="eta_max",  type=float,  help="maximum eta for neutrino to pass", default=10.)
parser.add_argument('-s',dest="seed",  type=int,  help="set seed", default=0)
parser.add_argument('-o', "--output", dest="output",  type=str,  help="output folder", default=".")
parser.add_argument('-l',"--low_info", dest="low_info", action='store_true',  help="store only nu and its mother", default=False)
parser.add_argument("--forward", dest="forward", action='store_true',  help="enable forward physics tune", default=False)
# for lhapdf, -X LHAPDF6:MMHT2014lo68cl (popular with LHC experiments, features LHC data till 2014)
# one PDF set, which is popular with IceCube, is HERAPDF15LO_EIG
# the default PDFpSet '13' is NNPDF2.3 QCD+QED LO

options = parser.parse_args()
ROOT.gRandom.SetSeed(options.seed)
X=ROOT.Pythia8Generator()

nunames=''
L=len(options.nu_flavour)
for i in range(0, L):
  if i==L-1: nunames +=nudict[options.nu_flavour[i]]
  else: nunames +=nudict[options.nu_flavour[i]]+'_'

# Make pp events
generator = ROOT.Pythia8.Pythia()
generator.readString("Random:setSeed = on")
generator.readString(f"Random:seed = {options.seed + 100}")
generator.settings.mode("Next:numberCount",options.heartbeat)
generator.settings.mode("Beams:idA",  2212)
generator.settings.mode("Beams:idB",  2212)
generator.readString("Beams:eCM = "+str(options.eCM));
# The Monash 2013 tune (#14) is set by default for Pythia above v8.200. 
# This tune provides slightly higher Ds and Bs fractions, in better agreement with the data.
# Tune setting comes before PDF setting!
generator.readString("Tune:pp = 14")
generator.readString("PDF:pSet = "+options.PDFpSet)
tag = 'nobias'
if options.charm:
     generator.readString("HardQCD:hardccbar = on")
     tag = 'ccbar'
elif options.beauty:
     generator.readString("HardQCD:hardbbbar = on")
     tag = 'bbbar'
elif options.hard:
     generator.readString("HardQCD:all = on")
     generator.readString("PhaseSpace:pTHatMin = 5.0")
     tag = 'hard'
     if options.unstablemesons:
          generator.readString("211:mayDecay = on"); 
          generator.readString("-211:mayDecay = on"); 
          generator.readString("211:mayDecay = on"); 
          generator.readString("130:mayDecay = on"); 
          generator.readString("321:mayDecay = on"); 
          generator.readString("-321:mayDecay = on"); 
          tag += "unstable_mesons"
elif options.weak:
     generator.readString("WeakBosonExchange:all  = on")
     tag = 'weak'
     if options.unstablemesons:
          generator.readString("211:mayDecay = on"); 
          generator.readString("-211:mayDecay = on"); 
          generator.readString("130:mayDecay = on"); 
          generator.readString("321:mayDecay = on"); 
          generator.readString("-321:mayDecay = on"); 
          tag += "unstable_mesons"
else:
     generator.readString("SoftQCD:inelastic = on")     
     if options.unstablemesons:
          generator.readString("211:mayDecay = on"); 
          generator.readString("-211:mayDecay = on"); 
          generator.readString("130:mayDecay = on"); 
          generator.readString("321:mayDecay = on"); 
          generator.readString("-321:mayDecay = on"); 
          tag += "unstable_mesons"
     if options.forward:
          generator.readString("BeamRemnants:dampPopcorn  = 0"); 
          generator.readString("BeamRemnants:hardRemnantBaryon = on"); 
          generator.readString("BeamRemnants:aRemnantBaryon = 0.68"); 
          generator.readString("BeamRemnants:bRemnantBaryon = 1.22"); 
          generator.readString("BeamRemnants:primordialKTsoft = 0.56");
          generator.readString("BeamRemnants:primordialKThard = 1.8");  
          generator.readString("BeamRemnants:halfScaleForKT = 10");  
          generator.readString("BeamRemnants:halfMassForKT = 1");        
          generator.readString("BeamRemnants:primordialKTremnant = 0.56");      
     # tag = 'soft'
     
generator.init()

rc = generator.next()
hname = 'pythia8_'+tag+'_PDFpset'+options.PDFpSet+'_'+nunames
hname = hname.replace('*','star')
hname = hname.replace('->','to')
hname = hname.replace('/','')
if not os.path.exists(options.output):
     os.makedirs(options.output)
fout = ROOT.TFile(os.path.join(options.output, hname+".root"),"RECREATE")
dTree = ROOT.TTree('NuTree', nunames)
dAnc = ROOT.TClonesArray("TParticle")
# AncstrBranch will hold the neutrino at 0th TParticle entry.
# Neutrino ancestry is followed backwards in evolution up to the colliding TeV proton
# and saved as 1st, 2nd,... TParticle entries of AncstrBranch branch
dAncstrBranch = dTree.Branch("Ancstr",dAnc,32000,-1)
# EvtId will hold event id
evtId = array('l', [0])
dEvtId = dTree.Branch("EvtId", evtId, "evtId/I")

timer = ROOT.TStopwatch()
timer.Start()

nMade = 0
py = generator
for n in range(int(options.firstEvent), int(options.firstEvent) + int(options.Np)):
  rc = py.next()
  nu_num = 0
  for ii in range(1,py.event.size()):
    # Ask for final state neutrino
#     if py.event[ii].id() in [211, -211, 221]:
#           print(py.event[ii].id(), py.event[ii].isFinal())
    if py.event[ii].isFinal() and py.event[ii].id() in options.nu_flavour:
     nu_num += 1
     evt = py.event[ii]
     eta = evt.eta()
     # print(py.event[ii].mother1())
     if (eta > options.eta_min) or (eta < -options.eta_min):
       dAnc.Clear()
       neut = ROOT.TParticle(evt.id(), evt.status(),
                            evt.mother1(),evt.mother2(),0,0,
                            evt.px(),evt.py(),evt.pz(),evt.e(),
                            evt.xProd(),evt.yProd(),evt.zProd(),evt.tProd())
       dAnc[0] = neut
       evtId[0] = n
       gm = py.event[ii].mother1()
     #   gm2 = py.event[ii].mother2()
     #   #if "5" == [ch_b for ch_b in str(py.event[gm].id())][0]:
     #   if np.abs(py.event[gm].id()) == 521:
     #      print(n, py.event[gm].id())
     #      while gm:
     #           evtM = py.event[gm]
     #           print(py.event[gm].id(), py.event[gm2].id())
     #           gm = py.event[gm].mother1()
     #           gm2 = py.event[gm].mother2()
       # Chain all mothers (gm)
       while gm:
          evtM = py.event[gm]
          # print(evtM.id())
          anc = ROOT.TParticle(evtM.id(),evtM.status(),
                               evtM.mother1(),evtM.mother2(),evtM.daughter1(),evtM.daughter2(),
                               evtM.px(),evtM.py(),evtM.pz(),evtM.e(),
                               evtM.xProd(),evtM.yProd(),evtM.zProd(),evtM.tProd())
          nAnc = dAnc.GetEntries()
          if dAnc.GetSize() == nAnc: dAnc.Expand(nAnc+10)
          dAnc[nAnc] = anc
          gm = py.event[gm].mother1()
          if options.low_info:
               break
       dTree.Fill()
#   if nu_num >= 1:
#      print(nu_num, f"neutrinos in {n} event")
  nMade+=1
fout.cd() 
dTree.Write()
         
generator.stat()

timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
totalXsec = 0   # unit = mb,1E12 fb
info = ROOT.generator_info(generator)
processes = info.codesHard()
for p in processes:
   print(info.nameProc(p), info.sigmaGen(p))
   totalXsec+=info.sigmaGen(p)   
# nobias: 78.4mb, ccbar=4.47mb, bbbar=0.35mb
print(info.sigmaGen())
IntLumi = options.Np / totalXsec * 1E-12

print("Saving to output %s neutrino flavour(s) having PDG ID(s)"%(nunames), options.nu_flavour)
print("simulated events = %i, equivalent to integrated luminosity of %5.2G fb-1. Real time %6.1Fs, CPU time %6.1Fs"%(options.Np,IntLumi,rtime,ctime))
# neutrino CC cross section about 0.7 E-38 cm2 GeV-1 nucleon-1, SND@LHC: 59mm tungsten 
# sigma_CC(100 GeV) = 4.8E-12  
print("corresponding to effective luminosity (folded with neutrino CC cross section at 100GeV) of %5.2G fb-1."%(IntLumi/4.8E-12))
with open(os.path.join(options.output, 'lumi.txt'), 'w') as f:
    print(f"{IntLumi}", file=f)  # Python 3.x

def debugging(g):
   generator.settings.listAll()
