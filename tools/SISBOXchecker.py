# ! /usr/bin/env python
# _*_ coding: UTF-8 _*_


# import modules
import time, sys, datetime, os, signal
import matplotlib.pyplot as plt
import numpy as np
sys.path.append('/home/amigos/NASCORX_System-master/base/')
import Cryo
sys.path.append('/home/amigos/NASCORX_System-master/device/')
import CPZ340816, CPZ3177

class Boxchecker(object):
    def __init__(self):
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    def Vrem_Vout_ratio_tune(self, ch, Vrem=5.0):
        DA = CPZ340816.cpz340816(dev=2)
        print('Now start tuning of the Vrem to Vout ratio (ch = '+str(ch)+')')
        print('Connect "Remote Controller" to the D/A Board.')
        print('Connect "Vmon" to the voltmeter.')
        print('Ready?: [yes]/no')
        sf = raw_input()
        if sf == 'no':
            quit()
        else:
            Vrem = float(Vrem)
            DA.set_voltage(voltage=Vrem, ch=ch)
            DA.set_output(onoff=1)
        while 1:
            Vnow = DA.query_voltage()
            print(Vnow)
            Vnow = round(float(Vnow[ch]), 3)
            print('........................')
            print('Now D/A output --> '+str(Vnow)+' V')
            print('Target voltage --> '+str(Vnow*0.3)+' V')
            print(' Finish Tuning: input "bien"')
            print(' Change the D/A Output: input 0 -- 10 [V]')
            ef = raw_input()
            if ef == 'bien':
                break
            elif 0.0<=float(ef)<=10.0:
                Vrem = float(ef)
                print(Vrem)
                DA.set_voltage(voltage=Vrem, ch=ch)
            else:
                pass
        DA.set_output(onoff=0)
        DA.close_board()
        print('Finish Tuning!')
        return

    def Remote_bias_check(self, ch, Vrange=[0, 10], average=5, pngpath='/home/amigos/data/SISboardcheck/'):
        idealratio = 3.0
        Vres = 0.2
        Vrres = 1.0
        if ch==0:
            DAch = 0
            VADch = 0
            IADch = 1
        else:
            DAch = 1
            VADch = 2
            IADch = 3
        t = datetime.datetime.now()
        ut = t.strftime('%Y%m%d_%H%M%S')
        filename = 'Remote_bias_check_ch'+str(ch)+ut+'.png'
        DA = CPZ340816.cpz340816(dev=2)
        AD = CPZ3177.cpz3177(dev=1)
        AD.set_mode(mode='diff')
        AD.set_input_range(Vrange='AD_5V')
        ADres = (5000./2**12)*1e-2
        Output_mon = np.array([])
        Outputerr_mon = np.array([])
        V_list = np.arange(Vrange[0], Vrange[1], Vres) # V
        print('Voltage SWEEP:'+str(V_list[0])+' to '+str(V_list[1])+' mV')
        print('======== START ========')
        DA.set_voltage(voltage=0, ch=DAch)
        DA.set_output(onoff=1)
        for v in V_list:
            print('V = '+str(round(v, 2))+' V')
            DA.set_voltage(voltage=v, ch=DAch)
            doutput = np.array([])
            time.sleep(0.1)
            for j in range(average):
                ret = AD.query_input() # V
                doutput = np.append(doutput, ret[VADch]*1e+1) # mV
            doutput_mean = np.mean(doutput, axis=0)
            doutput_std = np.std(doutput, axis=0)
            Output_mon = np.append(Output_mon, doutput_mean)
            if doutput_std>ADres:
                Outputerr_mon = np.append(Outputerr_mon, doutput_std)
            else:
                Outputerr_mon = np.append(Outputerr_mon, ADres)
        V_rlist = np.arange(Vrange[0], Vrange[1], Vrres)
        V_rlist = np.sort(V_rlist)[::-1]
        for v in V_rlist:
            print('V = '+str(round(v, 2))+' mV')
            DA.set_voltage(voltage=v, ch=DAch)
            time.sleep(0.1)
        DA.close_board()
        AD.close_board()
        print('======== END ========')
        plt.errorbar(V_list, Output_mon, yerr=Outputerr_mon, fmt='.', ecolor='red', color='red', label='ch='+str(DAch))
        plt.plot([0, V_list.max()], [0, V_list.max()*idealratio], linestyle='-', color='green', linewidth=1.0, label='Target Ratio='+str(round(idealratio, 2)))
        plt.title('Remote Bias Check'+t.strftime('%Y/%m/%d/ %H:%M:%S'))
        plt.xlim(0, V_list.max())
        plt.ylim(Output_mon.min(), Output_mon.max())
        plt.xlabel('D/A Voltage [V]')
        plt.ylabel('Output Bias Voltage [mV]')
        plt.grid(True)
        plt.legend(loc='upper left')
        plt.savefig(pngpath+filename)
        plt.show()

    def IVtrace(self, ch, Vrange=[0, 30], average=5, pngpath='/home/amigos/data/SISboardcheck/'):
        Vres = 1.0
        Vrres = 5.0
        VADres = (5000./2**12)*1e-2 # mV
        IADres = (5000./2**12) # uA
        if ch==0:
            DAch = 0
            VADch = 0
            IADch = 1
        else:
            DAch = 1
            VADch = 2
            IADch = 3
        t = datetime.datetime.now()
        ut = t.strftime('%Y%m%d_%H%M%S')
        filename = 'R50ohm_ch'+str(ch)+ut+'.png'
        box = Cryo.mixer()    
        V_mon = np.array([])
        Verr_mon = np.array([])
        I_mon = np.array([])
        Ierr_mon = np.array([])
        V_list = np.arange(Vrange[0], Vrange[1], Vres)
        print('Voltage SWEEP:'+str(V_list[0])+' to '+str(V_list[1])+' mV')
        print('======== START ========')
        for v in V_list:
            print('V = '+str(round(v, 2))+' mV')
            box.set_sisv(Vmix=v, ch=DAch)
            dV = np.array([])
            dI = np.array([])
            time.sleep(0.1)
            for j in range(average):
                ret = box.monitor_sis()
                dV = np.append(dV, ret[VADch]*1e+1)
                dI = np.append(dI, ret[IADch]*1e+3)
            dV_mean = np.mean(dV, axis=0)
            dV_std = np.std(dV, axis=0)
            V_mon = np.append(V_mon, dV_mean)
            if dV_std>VADres:
                Verr_mon = np.append(Verr_mon, dV_std)
            else:
                Verr_mon = np.append(Verr_mon, VADres)            
            dI_mean = np.mean(dI, axis=0)
            dI_std = np.std(dI, axis=0)
            I_mon = np.append(I_mon, dI_mean)
            if dI_std>IADres:
                Ierr_mon = np.append(Ierr_mon, dI_std)
            else:
                Ierr_mon = np.append(Ierr_mon, IADres)
        R_mon = V_mon/I_mon*1e+3
        meanR = np.mean(R_mon, axis=0)
        V_rlist = np.arange(Vrange[0], Vrange[1], Vrres)
        V_rlist = np.sort(V_rlist)[::-1]
        for v in V_rlist:
            print('V = '+str(round(v, 2))+' mV')
            box.set_sisv(Vmix=v, ch=DAch)
            time.sleep(0.1)
        print('======== END ========')
        plt.errorbar(V_mon, I_mon, xerr=Verr_mon, yerr=Ierr_mon, fmt='.', ecolor='red', color='red', label='ch='+str(DAch))
        plt.plot([0, V_mon.max()], [0, V_mon.max()/meanR*1e+3], linestyle='-', color='green', linewidth=1.0, label='Rmean='+str(round(meanR, 3)))
        plt.title('50 ohm I-V '+t.strftime('%Y/%m/%d/ %H:%M:%S'))
        plt.xlim(0, V_mon.max())
        plt.ylim(I_mon.min(), I_mon.max())
        plt.xlabel('Bias Voltage [mV]')
        plt.ylabel('Bias Current [uA]')
        plt.grid(True)
        plt.legend(loc='upper left')
        plt.savefig(pngpath+filename)
        plt.show()

if __name__ == '__main__':
    testport = 1
    a = Boxchecker()
    a.Vrem_Vout_ratio_tune(ch=testport)
    a.Remote_bias_check(ch=testport)
    a.IVtrace(ch=testport)

# written by K.Urushihara
