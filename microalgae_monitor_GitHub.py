# -*- coding: utf-8 -*-

import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')


from gi.repository import Gtk, GLib, Gio, Adw,Gdk, Graphene
from gi.repository import Pango
import datetime
from time import strftime
from pathlib import Path
import serial
import glob
import os.path
from pymodbus.client import ModbusSerialClient
import struct #Importar para hacer conversiones a flotante big endian

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        str_title ='Microalgae monitoring system'
        self.set_title(str_title)

        #Layout main window
        hbox_main = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox_main.props.margin_start = 24
        hbox_main.props.margin_end = 24
        hbox_main.props.margin_top = 24
        hbox_main.props.margin_bottom = 24
        self.set_child(hbox_main)
        #Layout to add columns to main window
        vbox_control = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        #Label for water temperature magnitude
        self.lbl_water_temperature_value = Gtk.Label(label = "0.0", 
                                               name ='labelWaterTemp')
        #Label for pH magnitude
        self.lbl_ph_value = Gtk.Label(label = "0.0", name ='labelPH')
        #Label for electrical conductiviy magnitude
        self.lbl_ec_value = Gtk.Label(label = "0.0", name ='labelEC')
        #Label for turbidity magnitude
        self.lbl_turbidity_value = Gtk.Label(label = "0.0", 
                                             name ='labelTurbidity')
        #Label for dissolved oxigen saturation magnitude 
        self.lbl_do_saturation_value = Gtk.Label(label = "0.0", 
                                                 name ='labelDOSAT')       
        #Label for dissolved oxigen concentration magnitude 
        self.lbl_do_concentration_value = Gtk.Label(label = "0.0", 
                                                 name ='labelDOCONC')       

        #Label for photosynthetic photon flux density magnitude
        self.lbl_ppfd_value = Gtk.Label(label = "0.0", name ='labelPPFD')
        #Label for irradiance magnitude
        self.lbl_irradiance_value = Gtk.Label(label = "0.0", 
                                              name ='labelIrradiance')
        #Label for air temperature magnitude
        self.lbl_air_temperature_value = Gtk.Label(label = "0.0", 
                                                   name ='labelAirTemp')

        #Label for date value
        now = datetime.datetime.now()        
        self.lbl_date_value = Gtk.Label(label = now.strftime("%m/%d/%Y"),
                                        name ='labelDate')

        #Label for time value
        self.lbl_time_value = Gtk.Label(label = now.strftime("%H:%M:%S"), 
                                        name ='labelTime')

        #Applying the css Provider
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('style_microalgae_monitor.css')
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), 
                        css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        lbl_title = Gtk.Label()
        lbl_title.set_css_classes(['title'])
        #Label for COM port
        lbl_com_port = Gtk.Label(label = 'COM Port: ')
        lbl_com_port.set_xalign(0.0) #Align left      
        vbox_control.append(lbl_com_port)
        #String for the COM Port
        self.com_port = None

        #Method for getting the port of the connected devices
        self.ports = self.serial_ports()
        model_port = Gtk.StringList()
        for com in self.ports:
            model_port.append(com)
        #Dropdown containing the ports of the connected devices
        self.port_dropdown = Gtk.DropDown(model = model_port)
        vbox_control.append(self.port_dropdown)
        
        #Radio buttons for selecting the operation mode
        self.frame_operation = Gtk.Frame()
        vbox_radio =Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.frame_operation.set_child(vbox_radio) 
        self.frame_operation.set_label("Operation: ")
        self.radio_single = Gtk.CheckButton(label="Single  ")
        self.radio_continuous = Gtk.CheckButton(label="Continuous  ")
        self.radio_continuous.set_group(self.radio_single)
        self.radio_continuous.set_active(True)
        vbox_radio.append(self.radio_single)
        vbox_radio.append(self.radio_continuous)
        vbox_control.append(self.frame_operation)

        self.frame_photoperiod = Gtk.Frame()
        vbox_photoperiod = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.frame_photoperiod.set_child(vbox_photoperiod)
        self.frame_photoperiod.set_label("Photoperiod: ")       
        lbl_init_photo = Gtk.Label(label = 'Initial time: ')
        vbox_photoperiod.append(lbl_init_photo)
        lbl_hour_minute = Gtk.Label(label = 'Hour Minutes')
        vbox_photoperiod.append(lbl_hour_minute)
        vbox_init_photoperiod = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,  spacing = 6)        
        sample_init_photo_hour= Gtk.SpinButton.new_with_range(0,23,1)
        sample_init_photo_hour.connect("value-changed",
                             self.on_init_photo_hour_changed)
        vbox_init_photoperiod.append(sample_init_photo_hour)
        sample_init_photo_minutes= Gtk.SpinButton.new_with_range(0,59,1)
        vbox_init_photoperiod.append(sample_init_photo_minutes)
        sample_init_photo_minutes.connect("value-changed",
                             self.on_init_photo_minutes_changed)
        vbox_photoperiod.append(vbox_init_photoperiod)
        lbl_final_photo = Gtk.Label(label = 'Final time: ')
        vbox_photoperiod.append(lbl_final_photo)         
        lbl_hour_minute = Gtk.Label(label = 'Hour Minutes')
        vbox_photoperiod.append(lbl_hour_minute)
        vbox_final_photoperiod = Gtk.Box(orientation = Gtk.Orientation.HORIZONTAL,  spacing = 6)
        sample_final_photo_hour= Gtk.SpinButton.new_with_range(0,23,1)
        vbox_final_photoperiod.append(sample_final_photo_hour)
        sample_final_photo_hour.connect("value-changed",
                             self.on_final_photo_hour_changed)
        sample_final_photo_minutes= Gtk.SpinButton.new_with_range(0,59,1)
        vbox_final_photoperiod.append(sample_final_photo_minutes)
        vbox_photoperiod.append(vbox_final_photoperiod)
        sample_final_photo_minutes.connect("value-changed",
                             self.on_final_photo_minutes_changed)
        self.check_photoperiod= Gtk.CheckButton(label="  Enable  ")
        self.check_photoperiod.set_active(False)
        vbox_photoperiod.append(self.check_photoperiod)
        vbox_control.append(self.frame_photoperiod)
        
        
        #Button Start
        self.btn_start = Gtk.Button(label = 'Start')
        self.btn_start.connect('clicked', self.on_button_start_clicked)
        vbox_control.append(self.btn_start)
        #Button Stop
        self.btn_stop = Gtk.Button(label = 'Stop')
        self.btn_stop.connect('clicked', self.on_button_stop_clicked)
        vbox_control.append(self.btn_stop)
        
        #Button Save
        self.btn_save = Gtk.Button(label = 'Save')
        self.btn_save.connect('clicked', self.on_button_save_clicked)
        vbox_control.append(self.btn_save) 
        
        hbox_main.append(vbox_control)
        #Second column with values
        vbox_column2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        #Frame date
        vbox_date = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6) 
        self.frame_date  = Gtk.Frame()
        self.frame_date.set_child(vbox_date) 
        self.frame_date.set_label("Date: ")
        vbox_date.append(self.lbl_date_value)
        vbox_date.props.margin_start = 10
        vbox_date.props.margin_end = 10
        vbox_date.props.margin_top = 10
        vbox_date.props.margin_bottom = 10      
        vbox_column2.append(self.frame_date)
        #Frame time
        vbox_time = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.frame_time  = Gtk.Frame()
        self.frame_time.set_child(vbox_time) 
        self.frame_time.set_label("Time: ")
        vbox_time.append(self.lbl_time_value)
        vbox_time.props.margin_start = 10
        vbox_time.props.margin_end = 10
        vbox_time.props.margin_top = 10
        vbox_time.props.margin_bottom = 10
        vbox_column2.append(self.frame_time)

        #Frame water temperature
        vbox_water_temperature = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                         spacing=6)
        self.frame_water_temperature  = Gtk.Frame()
        self.frame_water_temperature.set_child(vbox_water_temperature) 
        self.frame_water_temperature.set_label("Water Temperature (°C): ")
        vbox_water_temperature.append(self.lbl_water_temperature_value)
        vbox_water_temperature.props.margin_start = 10
        vbox_water_temperature.props.margin_end = 10
        vbox_water_temperature.props.margin_top = 10
        vbox_water_temperature.props.margin_bottom = 10
        vbox_column2.append(self.frame_water_temperature)
        
        #pH
        vbox_ph= Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.frame_ph  = Gtk.Frame()
        self.frame_ph.set_child(vbox_ph) 
        self.frame_ph.set_label("pH: ")
        vbox_ph.append(self.lbl_ph_value)
        vbox_ph.props.margin_start = 10
        vbox_ph.props.margin_end = 10
        vbox_ph.props.margin_top = 10
        vbox_ph.props.margin_bottom = 10
        vbox_column2.append(self.frame_ph)

        #EC
        vbox_ec= Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.frame_ec  = Gtk.Frame()
        self.frame_ec.set_child(vbox_ec) 
        self.frame_ec.set_label("EC (us/cm): ")
        vbox_ec.append(self.lbl_ec_value)
        vbox_ec.props.margin_start = 10
        vbox_ec.props.margin_end = 10
        vbox_ec.props.margin_top = 10
        vbox_ec.props.margin_bottom = 10
        vbox_column2.append(self.frame_ec)

         #Frame turbidity
        vbox_turbidity = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.frame_turbidity  = Gtk.Frame()
        self.frame_turbidity.set_child(vbox_turbidity) 
        self.frame_turbidity.set_label("Turbidity (NTU): ")
        vbox_turbidity.append(self.lbl_turbidity_value)
        vbox_turbidity.props.margin_start = 10
        vbox_turbidity.props.margin_end = 10
        vbox_turbidity.props.margin_top = 10
        vbox_turbidity.props.margin_bottom = 10
        vbox_column2.append(self.frame_turbidity)

        #Appending to the main layout the second column
        hbox_main.append(vbox_column2)       
        
        #Third column with values
        vbox_column3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        #Frame dissolved oxygen saturation
        vbox_do_saturation = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                     spacing=6)
        self.frame_do_saturation  = Gtk.Frame()
        self.frame_do_saturation.set_child(vbox_do_saturation) 
        self.frame_do_saturation.set_label("DO Saturation (%): ")
        vbox_do_saturation.append(self.lbl_do_saturation_value)
        vbox_do_saturation.props.margin_start = 10
        vbox_do_saturation.props.margin_end = 10
        vbox_do_saturation.props.margin_top = 10
        vbox_do_saturation.props.margin_bottom = 10
        vbox_column3.append(self.frame_do_saturation)

        #Frame dissolved oxygen concentration
        vbox_do_concentration = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                     spacing=6)
        self.frame_do_concentration  = Gtk.Frame()
        self.frame_do_concentration.set_child(vbox_do_concentration) 
        self.frame_do_concentration.set_label("DO Concentration (mg/L): ")
        vbox_do_concentration.append(self.lbl_do_concentration_value)
        vbox_do_concentration.props.margin_start = 10
        vbox_do_concentration.props.margin_end = 10
        vbox_do_concentration.props.margin_top = 10
        vbox_do_concentration.props.margin_bottom = 10
        vbox_column3.append(self.frame_do_concentration)

        #Frame photosynthetic photon flux density
        vbox_ppfd = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                     spacing=6)
        self.frame_ppfd  = Gtk.Frame()
        self.frame_ppfd.set_child(vbox_ppfd) 
        self.frame_ppfd.set_label("PPFD (umol/cm^2s): ")
        vbox_ppfd.append(self.lbl_ppfd_value)
        vbox_ppfd.props.margin_start = 10
        vbox_ppfd.props.margin_end = 10
        vbox_ppfd.props.margin_top = 10
        vbox_ppfd.props.margin_bottom = 10
        vbox_column3.append(self.frame_ppfd)

        #Frame irradiance
        vbox_irradiance = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                     spacing=6)
        self.frame_irradiance  = Gtk.Frame()
        self.frame_irradiance.set_child(vbox_irradiance) 
        self.frame_irradiance.set_label("Irradiance (W/m^2): ")
        vbox_irradiance.append(self.lbl_irradiance_value)
        vbox_irradiance.props.margin_start = 10
        vbox_irradiance.props.margin_end = 10
        vbox_irradiance.props.margin_top = 10
        vbox_irradiance.props.margin_bottom = 10
        vbox_column3.append(self.frame_irradiance)
        
        #Frame air temperature
        vbox_air_temperature = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                                         spacing=6)
        self.frame_air_temperature  = Gtk.Frame()
        self.frame_air_temperature.set_child(vbox_air_temperature) 
        self.frame_air_temperature.set_label("Air Temperature (°C): ")
        vbox_air_temperature.append(self.lbl_air_temperature_value)
        vbox_air_temperature.props.margin_start = 10
        vbox_air_temperature.props.margin_end = 10
        vbox_air_temperature.props.margin_top = 10
        vbox_air_temperature.props.margin_bottom = 10
        vbox_column3.append(self.frame_air_temperature)

        #Appending to the main layout the third column
        hbox_main.append(vbox_column3)

        #Auxiliary instance variables
        self.period = 10000
        self.count = 1        
        self.master = None        
        self.stp_acq = False
        self.baud_rate = 9600
        self.flag_continue_reading = True
        self.take_data = False
        self.flag_continuous_run = True
        self.flag_single_run = False
        
        self.water_temperature_value = 0
        self.ph_value = 0
        self.ec_value = 0
        self.tu_value = 0
        self.temp_turbidity_value = 0
        self.do_saturation_value = 0
        self.do_concentration_value = 0
        self.ppfd_value = 0
        self.irradiance_value = 0
        self.air_temperature_value = 0

        self.flag_photoperiod = False
        self.init_photo_hour_int_value = 0
        self.init_photo_minutes_int_value = 0
        self.final_photo_hour_int_value = 0
        self.final_photo_minutes_int_value = 0
        self.str_date = ""
        self.str_time = ""
        self.status_first_relay = False        
        self.str_values = ""
        self.lst_values = []

        self.n_readings = 9 #Number of readings realized by the system

        self.str_header = "Date,Time,WaterTemp(C),AirTemp(C),Relay"
        self.str_header+= ",pH,EC(us/cm),Turbidity(NTU),"
        self.str_header+="TempTurbidity(C),DOSat(%),DO(mg/L)"
        self.str_header+=",PPFD(umol/cm^2s),Irradiance(W/m^2)\n"   
       

        #Setting the Adwaita dark theme
        app = self.get_application()
        sm = app.get_style_manager()
        sm.set_color_scheme(Adw.ColorScheme.PREFER_DARK)

    def on_button_start_clicked(self, _widget):
        print('Start')
        self.flag_continue_reading = True
        self.values = []
        self.count = 0  

        try:
            self.port_index = self.port_dropdown.get_selected()
            self.com_port =str(self.ports[self.port_index])
            print("COM port:", self.com_port)
        except:
            self.com_port = None
        if (self.master != None):
            self.master.close()
            self.master = None
        if (self.master == None):
            try:                       
                self.take_data = True
                self.flag_continue_reading = True                
            except:
                self.take_data = False
                self.flag_continue_reading = False
        if (self.take_data == True and self.flag_continue_reading == True):
            pass

        GLib.timeout_add(self.period,self.on_running_task)
    
    def on_running_task(self):
        if (self.take_data == True):           
            #print("self.count ", self.count)
            if (self.count%self.n_readings != 0):
                self.now = datetime.datetime.now()
                self.str_date = str(self.now.strftime("%m/%d/%Y"))
                self.lbl_date_value.set_label(self.str_date) 
                self.str_time = str(self.now.strftime("%H:%M:%S"))
                self.lbl_time_value.set_label(self.str_time)
                #print("Date and time label changed")
            if (self.count%self.n_readings == 1):
                #print("Reading temperature")
                try:
                    if (self.master != None):
                        try:
                            self.master.close()
                        except:
                            pass
                    self.master = ModbusSerialClient(port=self.com_port,
                                timeout=2, 
                                baudrate = self.baud_rate,
                                bytesize=8, 
                                parity='N',
                                stopbits=1)
                    self.master.connect()
                    read_registers = self.master.read_input_registers(address=0,
                                  count=2, device_id=1)
                    self.water_temperature_value = float(read_registers.registers[0])/10
                    #print(self.water_temperature_value)
                    self.lbl_water_temperature_value.set_label(str(self.water_temperature_value))
                    self.air_temperature_value = float(read_registers.registers[1])/10
                    #print(self.air_temperature_value)
                    self.lbl_air_temperature_value.set_label(str(self.air_temperature_value))
                    self.master.close()
                    self.master = None
                except:
                    print("Bad reading temperture")
        
            #Verify if the photoperiod is activated
            if (self.check_photoperiod.get_active() ==True and self.count%self.n_readings == 2):
                print("Photoperiod")
                initial_time = datetime.time(self.init_photo_hour_int_value,
                                        self.init_photo_minutes_int_value,0,0)
                #print("initial_time ", initial_time)
                final_time = datetime.time(self.final_photo_hour_int_value,
                                        self.final_photo_minutes_int_value,0,0)
                #print("final_time ", final_time)
                compare = final_time > initial_time
                #print("Compare " , compare)
                if (compare == True):
                    actual_time = datetime.time(int(self.now.strftime("%H")),
                                        int(self.now.strftime("%M")),0,0)
                    print("actual_time ", actual_time)
                    print(actual_time > initial_time and actual_time < final_time)
                    if (actual_time > initial_time and actual_time < final_time):
                        print("Changing relay")
                        try:
                            if (self.master != None):
                                try:
                                    self.master.close()
                                except:
                                    pass
                            self.master = ModbusSerialClient(port=self.com_port,
                                timeout=2, 
                                baudrate = self.baud_rate,
                                bytesize=8, 
                                parity='N',
                                stopbits=1)
                            self.master.connect()
                            status = self.master.read_coils(address=0, count = 2, device_id=32)
                            self.status_first_relay=status.bits[0]
                            status_second_relay=status.bits[1]
                            if (self.status_first_relay == False):
                                wc = self.master.write_coils(address=0, values=[True,False], device_id=32)
                            self.master.close()
                            self.master = None
                        except:
                            pass
                    else:
                        try:
                            if (self.master != None):
                                try:
                                    self.master.close()
                                except:
                                    pass
                            self.master = ModbusSerialClient(port=self.com_port,
                                timeout=2, 
                                baudrate = self.baud_rate,
                                bytesize=8, 
                                parity='N',
                                stopbits=1)
                            self.master.connect()
                            status = self.master.read_coils(address=0, count = 2, device_id=32)
                            self.status_first_relay=status.bits[0]
                            status_second_relay=status.bits[1]
                            if (self.status_first_relay == True):
                                wc = self.master.write_coils(address=0, values=[False,False], device_id=32)
                            self.master.close()
                            self.master = None
                        except:
                            pass
            if (self.check_photoperiod.get_active() == False and self.count%self.n_readings == 2):
                #print("Condition self.check false")
                try:
                    if (self.master != None):
                        try:
                            self.master.close()
                        except:
                            pass
                    self.master = ModbusSerialClient(port=self.com_port,
                                timeout=2, 
                                baudrate = self.baud_rate,
                                bytesize=8, 
                                parity='N',
                                stopbits=1)
                    self.master.connect()
                    status = self.master.read_coils(address=0, count = 2, device_id=32)
                    self.status_first_relay=status.bits[0]
                    status_second_relay=status.bits[1]
                    if (self.status_first_relay == True):
                        wc = self.master.write_coils(address=0, values=[False,False], device_id=32)
                    self.master.close()
                    self.master = None
                except:
                    pass

            if (self.count%self.n_readings == 3):
                #print("Reading pH y EC")
                try:
                    if (self.master != None):
                        try:
                            self.master.close()
                        except:
                            pass
                    self.master = ModbusSerialClient(port=self.com_port,
                                timeout=2, 
                                baudrate = self.baud_rate,
                                bytesize=8, 
                                parity='N',
                                stopbits=1)
                    self.master.connect()
                    read_registers = self.master.read_holding_registers(address=0,
                                  count=3, device_id=2)
                    self.ph_value = float(read_registers.registers[0])/100
                    #print("self.ph_value",self.ph_value)
                    self.lbl_ph_value.set_label(str(self.ph_value))
                    self.ec_value = float(read_registers.registers[1])/10
                    #print("self.ec_value ", self.ec_value)
                    self.lbl_ec_value.set_label(str(self.ec_value))
                    self.master.close()
                    self.master = None
                except:
                    print("Bad reading of pH and EC sensors")
            if (self.count%self.n_readings == 4):
                #print("Reading turbidity")
                try:
                    if (self.master != None):
                        try:
                            self.master.close()
                        except:
                            pass
                    self.master = ModbusSerialClient(port=self.com_port,
                                timeout=2, 
                                baudrate = self.baud_rate,
                                bytesize=8, 
                                parity='N',
                                stopbits=1)
                    self.master.connect()
                    read_registers = self.master.read_holding_registers(address=0,
                                  count=2, device_id=3)
                    self.tu_value = float(read_registers.registers[0])/10
                    print("self.tu_value",self.tu_value)
                    self.lbl_turbidity_value.set_label(str(self.tu_value))
                    self.temp_turbidity_value = float(read_registers.registers[1])/10
                    print("temp_turbidity ", self.temp_turbidity_value)                    
                    self.master.close()
                    self.master = None
                except:
                    print("Bad reading of turbidity sensor")        
            if (self.count%self.n_readings == 5):
                #print("Reading dissolved oxygen")
                try:
                    if (self.master != None):
                        try:
                            self.master.close()
                        except:
                            pass
                    self.master = ModbusSerialClient(port=self.com_port,
                                timeout=2, 
                                baudrate = self.baud_rate,
                                bytesize=8, 
                                parity='N',
                                stopbits=1)
                    self.master.connect()
                    read_registers = self.master.read_holding_registers(address=0,
                                  count=6, device_id=4)
                    v0 = str(hex(read_registers.registers[0]))
                    v0 = v0[2:]
                    #Converting the second hexadecimal value of DO saturation to a string
                    v1 = str(hex(read_registers.registers[1]))
                    v1 = v1[2:]
                    #Concatenation of both values
                    v_oxi_sat = v0 + v1
                    str_v_oxi_sat = '{0:.2f}'.format(struct.unpack('!f', bytes.fromhex(v_oxi_sat))[0])
                    self.do_saturation_value = float(str_v_oxi_sat)
                    print("self.do_saturation_value",self.do_saturation_value)
                    self.lbl_do_saturation_value.set_label(str(self.do_saturation_value))
                    #Conversion to string of the first hexadecimal value of DO concentration
                    v2 = str(hex(read_registers.registers[2]))
                    v2 = v2[2:]
                    #Conversion to string of the second hexadecimal value of DO concentration
                    v3 = str(hex(read_registers.registers[3]))
                    v3 = v3[2:]
                    #Concatenation of both values
                    v_oxi_concentration = v2 + v3
                    str_v_oxi_concentration = '{0:.2f}'.format(struct.unpack('!f', bytes.fromhex(v_oxi_concentration))[0])
                    self.do_concentration_value = float(str_v_oxi_concentration)
                    print("self.do_concentration_value",self.do_concentration_value)
                    self.lbl_do_concentration_value.set_label(str(self.do_concentration_value))
                    v4 = str(hex(read_registers.registers[4]))
                    v4 = v4[2:]
                    """
                    #Conversion to string of the second hexadecimal temperature value
                    v5 = str(hex(read_registers.registers[5]))
                    v5 = v5[2:]
                    #Concatenation of both values
                    v_temperature = v4 + v5
                    #print("temperature DO sensor",struct.unpack('!f', bytes.fromhex(v_temperature))[0])
                    str_temp_do='{0:.2f}'.format(struct.unpack('!f', bytes.fromhex(v_temperature))[0])
                    print(" str_temp_do",str_temp_do)
                    """
                    self.master.close()
                    self.master = None
                except:
                    print("Bad reading of DO sensor")
            if (self.count%self.n_readings == 6):
                #print("Reading PPFD")
                try:
                    if (self.master != None):
                        try:
                            self.master.close()
                        except:
                            pass
                    self.master = ModbusSerialClient(port=self.com_port,
                                timeout=2, 
                                baudrate = self.baud_rate,
                                bytesize=8, 
                                parity='N',
                                stopbits=1)
                    self.master.connect()
                    read_registers = self.master.read_holding_registers(address=0,
                                  count=1, device_id=5)
                    self.ppfd_value = float(read_registers.registers[0])
                    print("self.ppfd_value",self.ppfd_value)
                    self.lbl_ppfd_value.set_label(str(self.ppfd_value))                   
                    self.master.close()
                    self.master = None
                except:
                    print("Bad reading of PPFD sensor")
            if (self.count%self.n_readings == 7):
                #print("Reading Irradiance")
                try:
                    if (self.master != None):
                        try:
                            self.master.close()
                        except:
                            pass
                    self.master = ModbusSerialClient(port=self.com_port,
                                timeout=2, 
                                baudrate = self.baud_rate,
                                bytesize=8, 
                                parity='N',
                                stopbits=1)
                    self.master.connect()
                    read_registers = self.master.read_holding_registers(address=0,
                                  count=1, device_id=6)
                    self.irradiance_value = float(read_registers.registers[0])
                    print("self.irradiance_value",self.irradiance_value)
                    self.lbl_irradiance_value.set_label(str(self.irradiance_value))                   
                    #time.sleep(self.time_sleep)
                    self.master.close()
                    self.master = None
                except:
                    print("Bad reading of Irradiance sensor")
            if (self.count%self.n_readings == 8):
                self.str_values =   self.str_date + "," + self.str_time + ","
                self.str_values  +=   str(self.water_temperature_value) + ","
                self.str_values += str(self.air_temperature_value) + ","
                self.str_values += str(int(self.status_first_relay)) + ","
                self.str_values += str(self.ph_value) + "," + str(self.ec_value) + ","
                self.str_values += str(self.tu_value) + "," + str(self.temp_turbidity_value) + ","
                self.str_values += str(self.do_saturation_value) + ","
                self.str_values += str(self.do_concentration_value) + "," + str(self.ppfd_value) + ","
                self.str_values += str(self.irradiance_value) + "\n"
                #print(self.str_values)
                #print("self.radio_continuous.get_active()",self.radio_continuous.get_active())
                if (self.radio_continuous.get_active() == True):                    
                    try:                                                                     
                        s1 = self.now.strftime("%m/%d/%Y,%H:%M:%S")
                        file_name = str(self.now.strftime("%m-%d-%Y"))
                        file_name = file_name +".csv"
                        #print("filename: ", file_name)
                        if (os.path.exists(file_name)==True):                              
                            str_val = self.str_values 
                            file = open(file_name, 'a')
                            file.write(str_val)
                            file.close()
                        else:                    
                            file = open(file_name, 'w')                                                     
                            file.write(self.str_header)
                            str_val = self.str_values
                            file.write(str_val)
                            file.close()    
                    except:
                        print("It couldn't save the data")
                else:
                    self.values.append(self.str_values)
        

        self.count = self.count + 1
        if (self.count == 90):
            self.count = 0
        if (self.flag_continue_reading == False):
            print('Stop')
            print()
        return self.flag_continue_reading

    def on_button_stop_clicked(self, _widget):
        print("Stop")     
        self.flag_continue_reading = False
    
                       
    def on_button_save_clicked(self, widget):
        print('Save')
        self.save_dialog = Gtk.FileDialog.new()
        self.save_dialog.set_title("Save file")
        self.save_dialog.save(self,None,self.save_dialog_save_callback)

    def save_dialog_save_callback(self,dialog,result):
        try:
            file = dialog.save_finish(result)
            if file is not None:
                #print(f"File path is {file.get_path()}")
                new_file = open(file.get_path(),'w')
                new_file.write(self.str_header)
                for i in range(len(self.values)):
                    new_file.write(self.values[i])
                new_file.close()
            # Handle loading file from here
        except GLib.Error as error:
            print(f"Error opening file:{error.message}")
    
    def on_failed_connection(self):
        failed_connection_dialog = Gtk.MessageDialog(transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Board communication error, no data will be taken!",
            title = "COM Error")
        failed_connection_dialog.run()
        failed_connection_dialog.destroy()

    def serial_ports(self) -> list:
        """ Lists serial port names    
            :raises EnvironmentError:
            On unsupported or unknown platforms
            :returns:
                A list of the serial ports available on the system
        """
        if sys.platform.startswith('win'):
            ports = ['COM%s' % (i + 1) for i in range(256)]
        elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
            # this excludes your current terminal "/dev/tty"
            ports = glob.glob('/dev/tty[A-Za-z]*')
        elif sys.platform.startswith('darwin'):
            ports = glob.glob('/dev/tty.*')
        else:
            raise EnvironmentError('Unsupported platform')

        result = []
        for port in ports:
            try:
                s = serial.Serial(port)
                s.close()
                result.append(port)
            except (OSError, serial.SerialException):
                pass
        return result
    
    def on_init_photo_hour_changed(self,spinbutton):
        self.init_photo_hour_int_value = spinbutton.get_value_as_int()
        #print(self.init_photo_hour_int_value)
    def on_init_photo_minutes_changed(self,spinbutton):
        self.init_photo_minutes_int_value = spinbutton.get_value_as_int()
        #print(self.init_photo_minutes_int_value)
    def on_final_photo_hour_changed(self,spinbutton):
        self.final_photo_hour_int_value = spinbutton.get_value_as_int()
        #print(self.final_photo_hour_int_value)
    def on_final_photo_minutes_changed(self,spinbutton):
        self.final_photo_minutes_int_value = spinbutton.get_value_as_int()
        #print(self.final_photo_minutes_int_value)        
        
class Application(Adw.Application):
    def __init__(self, *args, **kwargs):
            super().__init__(application_id="com.example.GtkApplication",*args,**kwargs)
            GLib.set_application_name("Microalgae monitoring")           
    def do_activate(self):
        window = MainWindow(application= self, title ="")
        window.present()
    def do_shutdown(self):
        Gtk.Application.do_shutdown(self)


if (__name__ == '__main__'):    
    app = Application()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)







