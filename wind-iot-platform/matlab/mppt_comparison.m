data = readtable('wind_forecast_data.csv');
time = data.time_seconds;
WindSpeed = data.actual_wind_speed;
forecast_wind = data.forecasted_wind_speed;

assignin('base', 'actual_wind_input', [time, WindSpeed]);
assignin('base', 'forecast_wind_input', [time, forecast_wind]);

simOut_baseline = sim('baseline_model');
power_baseline = simOut_baseline.P_baseline.Data;
time = simOut_baseline.P_baseline.Time;

simOut_forecast = sim('forecast_model');
power_forecast = simOut_forecast.P_forecast.Data;

energy_baseline = trapz(time, power_baseline);
energy_forecast = trapz(time, power_forecast);
improvement_pct = (energy_forecast - energy_baseline) / energy_baseline * 100;
fprintf('Improvement: %.2f%%\n', improvement_pct);

writetable(table(time, power_baseline, power_forecast, ...
    'VariableNames', {'time','power_baseline','power_forecast'}), ...
    'mppt_results.csv');

writetable(table(energy_baseline, energy_forecast, improvement_pct), ...
    'mppt_summary_results.csv');
