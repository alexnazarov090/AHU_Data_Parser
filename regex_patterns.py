
ahu_sections = [
    ('AHU_NAME',   r'(?:Позиция_*(?:заказчика)?:|(?:Номер|Название|№|Имя)?_?(?:установк[иа]|систем[ыа]))|(?:Position)'),
    ('SILENCER',   r'(?:блок_)?шумоглушител[ья]|silencer|sound attenuator'),
    ('FILTER',   r'фильтр(?![аовму]+)_?(?:приточный|вытяжной)?$|^filter$'),
    ('PANEL_FILTER_STAGE1',   r'(?:панельный_)?фильтр(?![аовму]+)_1_ступени'),
    ('BAG_FILTER_STAGE2',   r'(?:карманный_)?фильтр(?![аовму]+)_2_ступени'),
    ('HEAT_RECOVERY_SUPPLY',   r'(?:нагреватель_)?гликол\.?(?:иевый)?_рекуператор(?![аовму]+)|(?:glycol_)?energy recovery'),
    ('HEAT_RECOVERY_EXHAUST',   r'(?:охладитель_)?гликол\.?(?:иевый)?_рекуператор(?![аовму]+)|(?:glycol_)?energy recovery'),
    ('HEATER',   r'(?:водяной_)?(?:на|подо|обо)греватель(?!_?гликол\.?(?:иевый)?_рекуператор)(?:_воздуха)?|(?:air_)?heater'),
    ('COOLER',   r'(?:водяной|фреоновый)?_?охладитель(?!_?гликол\.?(?:иевый)?_рекуператор)(?:_воздуха)?|(?:Water|DX)_?(air_)?cooler'),
    ('FAN',   r'вентилятор(?![аовму]+)|fan'),
    ]

hex_pars_air = [
    ('HEX_AIR_FLOW_RATE',   r'(?:расход(?!_среды)_воздуха)'),
    ('HEX_AIR_VELOCITY',   r'(?:скорость(?!_среды|_теплоносителя)_воздуха)'),
    ('HEX_INLET_TEMP',   r'(?:температура_)?воздуха?_на_входе|◦t_нар[ужного]*\.?_воз[духа]*\.?'),
    ('HEX_OUTLET_TEMP',   r'(?:температура_)?воздуха?_на_выходе|◦t_вых[одного]*\.?_воз[духа]*\.?'),
    ('HEX_AIR_PR_DROP',   r'(?:пот\.?ер[ия]|пад\.?ение)?_?(?:давл\.?(?:ения)|напора)?_?(?:по_воздуху|воз[духа]*\.?)'),
    ('HEX_CAPACITY',   r'(?:пр[оизводительно-]+сть|мощность)')
]

hex_pars_water = [
    ('HEX_MEDIUM',   r'(?:вид|тип)?_?(?:теплоносител[ья]$|среда$)'),
    ('HEX_MEDIUM_FLOW_RATE',   r'(?:расход(?!_воздуха)_(?:среды|воды|теплоносителя))'),
    ('HEX_MEDIUM_VELOCITY',   r'(?:скорость(?!_воздуха)(?:_теплоносителя))'),
    ('HEX_MEDIUM_INLET_TEMP',   r'(?:температура_)?(?:теплоносител[ья]|сред[ыа]|вод[ыа])(?:_на_)?входе?|◦t_вх[одного]*\.?_?(?:теплоносител[ья]|сред[ыа]|вод[ыа])'),
    ('HEX_MEDIUM_OUTLET_TEMP',   r'(?:температура_)?(?:теплоносител[ья]|сред[ыа]|вод[ыа])(?:_на_)?выходе?|◦t_вых[одного]*\.?_?(?:теплоносител[ья]|сред[ыа]|вод[ыа])'),
    ('HEX_MEDIUM_PR_DROP',   r'(?:пот\.?(?:ер[ия])?_?(давл\.?(?:ения)|напора)?_?(?:теплоносител[ья]|сред[ыа]|вод[ыа]))'),
    ('HEX_MEDIUM_HEX_VOLUME',   r'(?:объем(?:_теплоносител[ья]|сред[ыа])?)'),
    ('HEX_ROWS',   r'(?:количество_)?ряд(?:ность|ов)'),
    ('HEX_INLET_DN',   r'(?:соединение|диаметр_подсоединения)_?(?:на_)?(?:вход[еа]?)?'),
    ('HEX_OUTLET_DN',   r'(?:соединение|диаметр_подсоединения)_?(?:на_)?(?:выход[еа]?)?'),
    ('HEX_WEIGHT',   r'масса|вес')
]

filter_pars = [
    ('FILTER_AIR_FLOW_RATE',   r'(?:расход(?!_среды)_воздуха)'),
    ('FILTER_AIR_PR_DROP',   r'(?:пот\.?ер[ия]|пад\.?ение)?_?(?:давл\.?(?:ения)|напора)?_?(?:по_воздуху|воз[духа]*\.?)'),
    ('FILTER_TYPE',   r'обозначение|наименование'),
    ('FILTER_CLASS',   r'класс_?(?:очистки|фильтра)?'),
    ('FILTER_WEIGHT',   r'масса|вес')
]

HEX_PARS_VALUES_REGEX = {
    'HEX_AIR_FLOW_RATE': r'^\d{0,4}[,.]?\d{1,4}',
    'HEX_AIR_VELOCITY': r'^\d{0,4}[,.]?\d{1,4}',
    'HEX_INLET_TEMP': r'^\-?\d{0,4}[,.]?\d{1,4}',
    'HEX_OUTLET_TEMP': r'^\-?\d{0,4}[,.]?\d{1,4}',
    'HEX_AIR_PR_DROP': r'^\d{0,4}[,.]?\d{1,4}',
    'HEX_CAPACITY': r'^\d{0,4}[,.]?\d{1,4}',
    'HEX_MEDIUM': r'^(?:\d{0,2}_?\%?_?(?:р-[аство]*р_)?(?:пропилен|этилен)гликол[ья]?)|вода',
    'HEX_MEDIUM_FLOW_RATE': r'^\d{0,4}[,.]?\d{1,4}',
    'HEX_MEDIUM_VELOCITY': r'^\d{0,4}[,.]?\d{1,4}',
    'HEX_MEDIUM_INLET_TEMP': r'^\-?\d{0,4}[,.]?\d{1,4}',
    'HEX_MEDIUM_OUTLET_TEMP': r'^\-?\d{0,4}[,.]?\d{1,4}',
    'HEX_MEDIUM_PR_DROP': r'^\d{0,4}[,.]?\d{1,4}',
    'HEX_MEDIUM_HEX_VOLUME': r'^\d{0,4}[,.]?\d{1,4}',
    'HEX_ROWS': r'^\d+',
    'HEX_INLET_DN': r'^[dnду]{0,2}_?\d{1,2}\/?\d{0,2}',
    'HEX_OUTLET_DN': r'^[dnду]{0,2}_?\d{1,2}\/?\d{0,2}',
    'HEX_WEIGHT': r'^\d{0,4}[,.]?\d{1,4}',
}

FILTER_PARS_VALUES_REGEX = {
    'FILTER_AIR_FLOW_RATE': r'^\d{0,4}[,.]?\d{1,4}',
    'FILTER_AIR_VELOCITY': r'^\d{0,4}[,.]?\d{1,4}',
    'FILTER_AIR_PR_DROP': r'^\d{0,4}[,.]?\d{1,4}',
    'FILTER_TYPE': r'[GFH]_?\d{1,2}',
    'FILTER_CLASS': r'EU_?\d{1,2}',
    'FILTER_WEIGHT': r'^\d{0,4}[,.]?\d{1,4}',
}

AHU_SEC_REGEX = '|'.join('(?P<%s>%s)+?' % pair for pair in ahu_sections)
HEX_PARS_AIR_REGEX = '|'.join('(?P<%s>%s)+?' % pair for pair in hex_pars_air)
HEX_PARS_WATER_REGEX = '|'.join('(?P<%s>%s)+?' % pair for pair in hex_pars_water)
FILTER_PARS_REGEX = '|'.join('(?P<%s>%s)+?' % pair for pair in filter_pars)
