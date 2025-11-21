// Données des pays et villes chargées dynamiquement depuis les unités consulaires actives

let COUNTRIES_CITIES = {};
let loadPromise = null;

async function loadCountriesCities() {
    if (loadPromise) {
        return loadPromise;
    }
    
    loadPromise = (async () => {
        try {
            const response = await fetch('/api/countries-cities');
            if (!response.ok) {
                throw new Error('Erreur lors du chargement des pays et villes');
            }
            
            COUNTRIES_CITIES = await response.json();
            return COUNTRIES_CITIES;
        } catch (error) {
            console.error('Erreur lors du chargement des pays et villes:', error);
            loadPromise = null;
            COUNTRIES_CITIES = {};
            return COUNTRIES_CITIES;
        }
    })();
    
    return loadPromise;
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

function findCitySelectForCountry(countrySelect, processedSelects) {
    if (countrySelect.id) {
        const possibleCityPatterns = [
            countrySelect.id.replace(/country/i, 'city'),
            countrySelect.id.replace(/pays/i, 'ville'),
            countrySelect.id.replace(/Country/i, 'City'),
            countrySelect.id.replace(/Pays/i, 'Ville')
        ];
        
        for (let pattern of possibleCityPatterns) {
            const citySelect = document.getElementById(pattern);
            if (citySelect && citySelect.tagName === 'SELECT' && !processedSelects.has(citySelect)) {
                return citySelect;
            }
        }
    }
    
    const immediateParent = countrySelect.closest('.grid, .flex, .form-group, [class*="col"]');
    if (immediateParent) {
        const siblingSelects = immediateParent.querySelectorAll('select');
        for (let select of siblingSelects) {
            if (select !== countrySelect && !processedSelects.has(select)) {
                const selectId = (select.id || '').toLowerCase();
                const selectName = (select.name || '').toLowerCase();
                if (selectId.includes('city') || selectId.includes('ville') ||
                    selectName.includes('city') || selectName.includes('ville')) {
                    return select;
                }
            }
        }
    }
    
    const formRow = countrySelect.parentElement;
    if (formRow) {
        const nextSibling = formRow.nextElementSibling;
        if (nextSibling) {
            const citySelect = nextSibling.querySelector('select');
            if (citySelect && !processedSelects.has(citySelect)) {
                const selectId = (citySelect.id || '').toLowerCase();
                const selectName = (citySelect.name || '').toLowerCase();
                if (selectId.includes('city') || selectId.includes('ville') ||
                    selectName.includes('city') || selectName.includes('ville')) {
                    return citySelect;
                }
            }
        }
    }
    
    return null;
}

document.addEventListener('DOMContentLoaded', function() {
    const allSelects = document.querySelectorAll('select');
    const processedSelects = new WeakSet();
    
    allSelects.forEach(function(select) {
        const selectId = (select.id || '').toLowerCase();
        const selectName = (select.name || '').toLowerCase();
        
        if ((selectId.includes('country') || selectId.includes('pays') ||
             selectName.includes('country') || selectName.includes('pays')) &&
            !processedSelects.has(select)) {
            
            const citySelect = findCitySelectForCountry(select, processedSelects);
            
            if (citySelect && !processedSelects.has(citySelect)) {
                processedSelects.add(select);
                processedSelects.add(citySelect);
                
                const initialCountry = select.dataset.initial || '';
                const initialCity = citySelect.dataset.initial || '';
                
                loadCountriesCities().then(() => {
                    populateCountrySelect(select, initialCountry);
                    
                    if (initialCountry) {
                        populateCitySelect(citySelect, initialCountry, initialCity);
                    }
                    
                    select.addEventListener('change', function() {
                        populateCitySelect(citySelect, this.value);
                    });
                }).catch(error => {
                    console.error('Erreur lors de l\'initialisation des dropdowns:', error);
                });
            }
        }
    });
});
