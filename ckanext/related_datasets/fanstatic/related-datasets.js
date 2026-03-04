/**
 * CKAN module: related-datasets
 *
 * Provides an autocomplete search widget to link datasets together.
 * - Searches datasets via CKAN API
 * - Shows selected datasets as tags with remove buttons
 * - Stores selected IDs in a hidden input for form submission
 */
ckan.module('related-datasets', function($) {
    return {
        options: {
            // Existing related datasets (JSON array of {id, name, title})
            existing: '[]',
            // Current dataset ID (to exclude from search results)
            currentDataset: ''
        },

        initialize: function() {
            $.proxyAll(this, /_on/);

            this.existingDatasets = [];
            try {
                this.existingDatasets = JSON.parse(this.options.existing);
            } catch(e) {
                this.existingDatasets = [];
            }

            this.selectedDatasets = {};
            this.searchInput = this.el.find('.related-datasets-search');
            this.resultsList = this.el.find('.related-datasets-results');
            this.selectedList = this.el.find('.related-datasets-selected');
            this.hiddenInput = this.el.find('.related-datasets-ids');

            // Load existing related datasets
            this._loadExisting();

            // Bind events
            this.searchInput.on('input', this._onSearchInput);
            this.searchInput.on('keydown', this._onSearchKeydown);

            // Close results when clicking outside
            $(document).on('click', this._onDocumentClick);
        },

        teardown: function() {
            $(document).off('click', this._onDocumentClick);
        },

        _onDocumentClick: function(e) {
            if (!this.el[0].contains(e.target)) {
                this.resultsList.empty().hide();
            }
        },

        _onSearchKeydown: function(e) {
            if (e.keyCode === 13) {
                e.preventDefault();
                return false;
            }
        },

        _searchTimer: null,

        _onSearchInput: function() {
            var query = this.searchInput.val().trim();
            var that = this;

            if (this._searchTimer) {
                clearTimeout(this._searchTimer);
            }

            if (query.length < 2) {
                this.resultsList.empty().hide();
                return;
            }

            this._searchTimer = setTimeout(function() {
                that._doSearch(query);
            }, 300);
        },

        _doSearch: function(query) {
            var that = this;
            var apiUrl = ckan.SITE_ROOT + '/api/3/action/package_search';

            $.ajax({
                url: apiUrl,
                data: {q: query, rows: 10},
                dataType: 'json',
                success: function(response) {
                    if (response.success) {
                        that._showResults(response.result.results);
                    }
                },
                error: function() {
                    that.resultsList.html('<li class="no-results">Errore nella ricerca</li>').show();
                }
            });
        },

        _showResults: function(datasets) {
            var that = this;
            this.resultsList.empty();

            var filtered = datasets.filter(function(ds) {
                return ds.id !== that.options.currentDataset &&
                       !that.selectedDatasets[ds.id];
            });

            if (filtered.length === 0) {
                this.resultsList.html('<li class="no-results">Nessun risultato</li>').show();
                return;
            }

            filtered.forEach(function(ds) {
                var li = $('<li class="related-dataset-result"></li>')
                    .text(ds.title || ds.name)
                    .attr('data-id', ds.id)
                    .attr('data-name', ds.name)
                    .attr('data-title', ds.title || ds.name)
                    .on('click', function() {
                        that._addDataset(ds.id, ds.name, ds.title || ds.name);
                        that.resultsList.empty().hide();
                        that.searchInput.val('');
                    });
                that.resultsList.append(li);
            });

            this.resultsList.show();
        },

        _loadExisting: function() {
            var that = this;
            this.existingDatasets.forEach(function(ds) {
                that._addDataset(ds.id, ds.name, ds.title || ds.name);
            });
        },

        _addDataset: function(id, name, title) {
            if (this.selectedDatasets[id]) {
                return;
            }

            var that = this;
            this.selectedDatasets[id] = {name: name, title: title};

            var tag = $('<span class="related-dataset-tag"></span>');
            tag.attr('data-id', id);

            var link = $('<a></a>')
                .attr('href', ckan.SITE_ROOT + '/dataset/' + name)
                .attr('target', '_blank')
                .text(title);
            tag.append(link);

            var removeBtn = $('<button type="button" class="related-dataset-remove" title="Rimuovi">&times;</button>');
            removeBtn.on('click', function() {
                that._removeDataset(id);
            });
            tag.append(removeBtn);

            this.selectedList.append(tag);
            this._updateHiddenInput();
        },

        _removeDataset: function(id) {
            delete this.selectedDatasets[id];
            this.selectedList.find('[data-id="' + id + '"]').remove();
            this._updateHiddenInput();
        },

        _updateHiddenInput: function() {
            var ids = Object.keys(this.selectedDatasets);
            this.hiddenInput.val(ids.join(','));
        }
    };
});
