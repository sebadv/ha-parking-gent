# Parking Occupancy Ghent

[![HACS Integration][hacs_badge]](https://github.com/hacs)
![Parkeerbezetting Gent Logo](custom_components/gent_parking/logo.png)


Parking Occupancy Ghennt is a Home Assistant custom integration that provides **live occupancy data** for parking garages in Ghent, Belgium. Once installed via HACS, you can select which garages to monitor, and Home Assistant will create a sensor for each, showing the current number of available parking spaces.

## Features

- **Live Updates**: Fetches real-time data every minute.  
- **Multi-Select**: Choose one or multiple garages to monitor.  
- **Sensor State**: Number of currently free parking spots.  
- **Attributes**:  
  - `capacity`: Total number of parking spaces in the garage  
  - `address`: Street address of the garage  
  - `operator`: Managing entity or operator  
  - `attribution`: Data provider attribution string  

## Installation

1. In Home Assistant, go to **HACS → Integrations → + → Custom Repositories**.  
2. Add the repository URL: `https://github.com/sebadv/ha-parking-gent`, set category to **Integration**, and click **Add**.  
3. Install **Parking Occupancy Ghent** from HACS.  
4. Restart Home Assistant.  
5. Navigate to **Settings → Devices & Services → Add Integration**, search for **Parking Occupancy Ghent**, and follow the setup flow.  

## Configuration

During setup, you will be presented with a list of all available parking garages in Ghent. Simply multi-select the garages you want to monitor. To add or remove garages later, go to the integration’s **Options**.

## Data Source

This integration uses data from the City of Ghent’s open data API:

- **API Endpoint**:  
  `https://data.stad.gent/api/explore/v2.1/catalog/datasets/bezetting-parkeergarages-real-time/records?limit=20`  
- **Documentation**:  
  https://data.stad.gent/api/explore/v2.1/documentation  

### Data Provider

**City of Ghent (Stad Gent)**

Data is provided under the [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

## License

This integration is released under the MIT License. See [LICENSE](LICENSE) for full details.

---

[hacs_badge]: https://img.shields.io/badge/HACS-Default-orange.svg
