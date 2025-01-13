import htcondor
import classad
import pandas as pd
import os
import glob
import numpy as np
import time

# run_tag = "test_condor"
#run_tag = "beauty_production_nue_100m_eta_g_4-0"
#run_tag = "hard_production_100m_eta_g_4-0_1"
#run_tag = "weak_production_nue_100m_eta_g_4-0"
# run_tag = "soft_production_nue_100m_eta_g_4-0_2"
run_tag = "soft_production_nutau_5000m_eta_g_7-0_forward_13012025"
# run_tag = "soft_production_numu_10m_eta_g_4-0_meson_decay"
debug = False
extra_fs_args = "-X LHAPDF6:MMHT2014lo68cl -EtaMin 7.0 -f 16 -f -16 --forward"
path_to_fs = "/afs/cern.ch/user/u/ursovsnd/SND"
path_to_env = "/cvmfs/sndlhc.cern.ch/SNDLHC-2024/June25/setUp.sh"

events_per_job = 1000000



output_dir = '/eos/user/u/ursovsnd/advsnd/pythia/'
log_dir = "/afs/cern.ch/user/u/ursovsnd/neutrino/pythia_flux/pycondor/logs"

# output_dir = os.path.join(output_dir, run_tag)
input_files_db = pd.read_csv('input_for_muon_prod.txt', header=None)
input_files_db.columns=['path', 'nEvents', 'id']

#print(input_files_db)

credd = htcondor.Credd()
credd.add_user_cred(htcondor.CredTypes.Kerberos, None)


files = glob.glob(os.path.join(log_dir, '*'))
# for f in files:
#     os.remove(f)

for _, row in input_files_db.iterrows():#fileN, path in enumerate(input_files_db['path'].to_list()):

    lPath = row['path']
    total_events = row['nEvents']
    fid = row['id']
    if not os.path.exists(os.path.join(log_dir,run_tag)):
        os.mkdir(os.path.join(log_dir,run_tag))
    job_template = {
        "executable": "start_FS.sh",      
        "arguments": f"{path_to_env} {path_to_fs} $(input_file_name) $(start_event) $(nEvents) $(seed) $(extra_fs_args)",          # we will pass in the value for this macro via itemdata
        "output": os.path.join(log_dir, f"{run_tag}/fs-{fid}-{run_tag}-$(ProcId).out"),  
        "error": os.path.join(log_dir, f"{run_tag}/fs-{fid}-{run_tag}-$(ProcId).err"),  
        "log": os.path.join(log_dir, f"{run_tag}/cat-{fid}-{run_tag}-$(ProcId).log"),              
        "should_transfer_files": "NO", 
        "request_cpus": "1",
        'MY.SendCredential': True,
        'environment' :f'"out_dir={os.path.join(output_dir, run_tag, str(fid))}/$(subjob)"',             
        "request_memory": "4096MB",       
        "request_disk": "1024MB",           
        "+JobFlavour": "tomorrow",
        "+MaxRuntime": 60*60*24*2,
    }

    iter_data = []#[{'input_file_name': str(path), 'subjob': str(subjob)} for subjob, path in enumerate(range(2))]
    for i in range(np.ceil(total_events / events_per_job).astype('int')):
        start_event = i * events_per_job
        nEvents = events_per_job if (start_event + events_per_job) <= total_events else (total_events - start_event)
        iter_data.append({'input_file_name':lPath, 'subjob': str(i), 'start_event': str(start_event), 'nEvents':str(nEvents), 'seed': str(i), 'extra_fs_args': extra_fs_args})

    if debug:
        iter_data = iter_data[:2]
        iter_data[0]['nEvents'] = '10'
        iter_data[1]['nEvents'] = '10'

    schedd = htcondor.Schedd()
    cat_job = htcondor.Submit(job_template)
    print(iter_data)
    submit_result = schedd.submit(cat_job, itemdata = iter(iter_data))  # submit one job for each item in the itemdata

    print(submit_result.cluster())

    if debug:
        break
    print(f"{fid} started")
    time.sleep(1)

def run_connmon(files, jobs_per_file=50, output=None):
    pass
def run_docker():
    pass


