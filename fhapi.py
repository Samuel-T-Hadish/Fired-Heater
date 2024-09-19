def Fired_Heater():
    '''Fired Heater Efficiency Calculation based on Direct method as Per API 560
        '''
print(Fired_Heater.__doc__)   
Fired_Heater()

import CoolProp.CoolProp as CP


    
Parameter_dict={'Ambient Temperature' : 26.7,                   # C 
                'Relative Humidity': 50,                           #  %       
                'Radiation loss': 0.05,                             # %
                'Oxygen content on wet basis': 5,                  # %
                'Flue gas exit temperature': 446,                  # C
                'CO2 Mass fraction': 0.1527,
                'H2O Mass fraction': 0.0715,
                'O2 Mass fraction': 0.062, 
                'N2 Mass fraction': 0.709, 
                'SO2 Mass fraction': 0.502e-2,
                'Combustion air temperature': 40,                # C
                'Fuel temperature': 25,                           # C
                'Fuel mass flow rate' : 12000,                     # kg/hr 
                'Datum temperature': 15,                           # C
                'hL': 38520.4,                                       # kJ/kg
                'Specific heat of Fuel': 1.7,                      # kJ/kg.K
                'Steam Mass Flow Rate': 4200,                      # kg
                'Enthalpy of steam': 2777,                         # kJ/kg
                'Flue Gas Mass': 239165.572,                       # kg
                'Wet Air Mass': 222965.572,                        # kg
                'Percentage of excess air': 0.4,                     # %
                'Humidity of air': 0.4,                            # kg h2o/ kg wet air
                'Psat': CP.PropsSI('P', 'T', 26.7+273.15, 'Q', 0, 'Water'),  #pa                    
                
            }    
molar_fraction_water_equivalent_to_humidity =  Parameter_dict['Relative Humidity'] * Parameter_dict['Psat']* 18/28/ 100/ 101325
print(f'X_h: {molar_fraction_water_equivalent_to_humidity }')
def energy_input_from_fuel(mfuel, hL, Cpf, X_h, tf, td, ta, mairwet, msteam, Hs, d_p = 2):   
    
    Hf = Cpf * (tf - td)
    
    H_fuel= (hL + Hf) * mfuel
    print(f'heat of fuel: {H_fuel: .1f} kJ/kg')
    
    MWair = (1-X_h) * 28.84 + X_h*18
    Mair = mairwet/MWair
    Cpair = 33.915 + 1.214e-3 * (ta + td)/2
    Cphum = 34.42 + 6.281e-4 * (ta + td)/2 + 5.6106e-6 * pow(((ta + td)/2), 2)
    Ha = ((1-X_h)*Cpair + X_h * Cphum)*(ta-td) * Mair
    print(f'Sensible heat of wet air: {Ha: .1f} kJ/kg')

    # atomizing medium sensible heat
    Hm = msteam * Hs
    print(f'Sensible heat of atomizing medium: {Hm: .1f} kJ/kg')

    # Total heat input
    Q_in = (H_fuel + Ha + Hm) 
    
    return round(Q_in, d_p)

Q_in = energy_input_from_fuel(Parameter_dict['Fuel mass flow rate'], Parameter_dict['hL'], Parameter_dict['Specific heat of Fuel'], molar_fraction_water_equivalent_to_humidity, Parameter_dict['Fuel temperature'], Parameter_dict['Datum temperature'], Parameter_dict['Combustion air temperature'] , Parameter_dict['Wet Air Mass'], Parameter_dict['Steam Mass Flow Rate'], Parameter_dict['Enthalpy of steam'] )
print(f"Heat input1: {Q_in} kJ/kg\n")


def Energy_Output(mfuel, hL, radiation_loss, tg, td, xc, m3, xo, xn, xh, xs, d_p = 2):
    # Molar heat of CO2
    Cpco2 = 43.2936 + 0.0115 * (tg + td)/2 - 818558.5/pow(((tg + td)/2), 2)
    Nco2 = xc * m3/44
    #sensible heat of CO2
    Hco2 = Nco2*Cpco2 * (tg - td)

    # Molar heat of O2
    Cpo2 = 34.627 + 1.0802e-3 * (tg + td)/2 - 785900/pow(((tg + td)/2), 2)
    No2 = xo * m3/32
    #sensible heat of O2
    Ho2 = No2*Cpo2 * (tg - td)

    # Molar heat of N2
    Cpn2 = 27.2155 + 4.187e-3 * (tg + td)/2 
    Nn2 = xn * m3/28
    #sensible heat of N2
    Hn2 = Nn2*Cpn2 * (tg - td)

    # Molar heat of H2O
    Cph2o = 34.417 + 6.281e-4 * (tg + td)/2 - 5.611e-6 * pow(((tg + td)/2), 2)
    Nh2o = xh * m3/18
    #sensible heat of H2O
    Hh2o = Nh2o*Cph2o* (tg - td)

    # Molar heat of SO2
    Cpso2 = 32.24 + 0.0222 * (tg + td)/2 - 3.475e-5 * pow(((tg + td)/2), 2)
    Nhso2 = xs * m3/64
    #sensible heat of H2O
    Hso2 = Nhso2 * Cpso2 * (tg - td)

    hs = Hco2 + Ho2 + Hn2 + Hh2o + Hso2
    print(f"Sensible heat of combustion gases: {hs: .1f} kJ/hr\n")

    # percentage of heat loses

    hr = radiation_loss * hL*mfuel
    print(f"Heat loses due to radiation: {hr: .1f} kJ/hr\n")

    Q_out = hs + hr

    # Useful energy: heat absorbed by heated fluid

    Qu = Q_in - Q_out
    return round(Qu, d_p)
Qu = Energy_Output(Parameter_dict['Fuel mass flow rate'], Parameter_dict['hL'], Parameter_dict['Radiation loss'], Parameter_dict['Flue gas exit temperature'], Parameter_dict['Datum temperature'], Parameter_dict['CO2 Mass fraction'], Parameter_dict['Flue Gas Mass'], Parameter_dict['O2 Mass fraction'], Parameter_dict['N2 Mass fraction'], Parameter_dict['H2O Mass fraction'], Parameter_dict['SO2 Mass fraction'])
print(f"Energy useful: {Qu: .1f} KJ/kg")

def efficiency_by_direct_method_Net(Qu, Q_in, d_p = 2):
    
    Net_Thermal_Efficiency = 100*(Qu/Q_in)

    return round(Net_Thermal_Efficiency, d_p)

Net_Thermal_Efficiency = efficiency_by_direct_method_Net(Qu, Q_in)
print(f"Net Efficiency by direct method: {Net_Thermal_Efficiency} %")

def efficiency_by_direct_method_Gross(Qu, Q_in, hL, X_h, d_p = 2):
    
    hH = hL + X_h * 2464.9
    #print(f'HHV: {hH: .1f} kJ/kg\n')
    #print(hL)
    
    Gross_Thermal_Efficiency = 100*(Qu/(Q_in-hL+hH))
    
    return round(Gross_Thermal_Efficiency, d_p)

Gross_Thermal_Efficiency = efficiency_by_direct_method_Gross(Qu, Q_in, Parameter_dict['hL'], molar_fraction_water_equivalent_to_humidity)
print(f"Gross Efficiency by direct method: {Gross_Thermal_Efficiency} %")

def efficiency_by_direct_method_Fuel(Qu, mfuel, hL, d_p = 2):
    
    Fuel_Efficiency = 100*(Qu/(hL*mfuel))
    return round(Fuel_Efficiency, d_p)

Fuel_Efficiency = efficiency_by_direct_method_Fuel(Qu, Parameter_dict['Fuel mass flow rate'], Parameter_dict['hL'])
print(f"Fuel Efficiency by direct method: {Fuel_Efficiency} %")



