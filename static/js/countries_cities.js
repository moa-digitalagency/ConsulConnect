// Données des pays et villes chargées dynamiquement depuis les unités consulaires actives

let COUNTRIES_CITIES = {};
let isDataLoaded = false;

async function loadCountriesCities() {
    if (isDataLoaded) {
        return COUNTRIES_CITIES;
    }
    
    try {
        const response = await fetch('/api/countries-cities');
        if (!response.ok) {
            throw new Error('Erreur lors du chargement des pays et villes');
        }
        
        COUNTRIES_CITIES = await response.json();
        isDataLoaded = true;
        return COUNTRIES_CITIES;
    } catch (error) {
        console.error('Erreur lors du chargement des pays et villes:', error);
        COUNTRIES_CITIES = {};
        return COUNTRIES_CITIES;
    }
}

function populateCountrySelect(selectElement, selectedCountry = null) {
    if (!selectElement) return;
    
    selectElement.innerHTML = '<option value="">Sélectionnez un pays</option>';
    
    const countries = Object.keys(COUNTRIES_CITIES).sort();
    countries.forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        if (selectedCountry && country === selectedCountry) {
            option.selected = true;
        }
        selectElement.appendChild(option);
    });
}

function populateCitySelect(selectElement, country, selectedCity = null) {
    if (!selectElement) return;
    
    selectElement.innerHTML = '<option value="">Sélectionnez une ville</option>';
    selectElement.disabled = !country;
    
    if (country && COUNTRIES_CITIES[country]) {
        const cities = COUNTRIES_CITIES[country].sort();
        cities.forEach(city => {
            const option = document.createElement('option');
            option.value = city;
            option.textContent = city;
            if (selectedCity && city === selectedCity) {
                option.selected = true;
            }
            selectElement.appendChild(option);
        });
    }
}

function setupCountryCitySelects(countrySelectId, citySelectId, initialCountry = null, initialCity = null) {
    const countrySelect = document.getElementById(countrySelectId);
    const citySelect = document.getElementById(citySelectId);
    
    if (!countrySelect || !citySelect) {
        console.error(`Éléments non trouvés: ${countrySelectId} ou ${citySelectId}`);
        return;
    }
    
    loadCountriesCities().then(() => {
        populateCountrySelect(countrySelect, initialCountry);
        
        if (initialCountry) {
            populateCitySelect(citySelect, initialCountry, initialCity);
        }
        
        countrySelect.addEventListener('change', function() {
            populateCitySelect(citySelect, this.value);
        });
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const countrySelect = document.getElementById('country') || document.getElementById('pays');
    const citySelect = document.getElementById('city') || document.getElementById('ville');
    
    if (countrySelect && citySelect) {
        const initialCountry = countrySelect.dataset.initial || null;
        const initialCity = citySelect.dataset.initial || null;
        
        loadCountriesCities().then(() => {
            populateCountrySelect(countrySelect, initialCountry);
            
            if (initialCountry) {
                populateCitySelect(citySelect, initialCountry, initialCity);
            }
            
            countrySelect.addEventListener('change', function() {
                populateCitySelect(citySelect, this.value);
            });
        });
    }
});
