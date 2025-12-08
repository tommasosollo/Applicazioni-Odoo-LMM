/**
 * SEO AI - SERP Preview Widget
 * Displays search engine result page preview for products
 */

odoo.define('ecommerce_seo_translator_pro.seo_preview', function(require) {
    'use strict';

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');
    const _t = core._t;

    const SEOPreview = AbstractAction.extend({
        template: 'seo.preview.template',

        init(parent, action) {
            this._super(parent, action);
            this.product_id = action.params.product_id;
        },

        start() {
            this._update_preview();
            return this._super();
        },

        _update_preview() {
            const self = this;

            this._rpc({
                route: '/seo-ai/meta-preview',
                params: {
                    product_id: this.product_id,
                },
            }).then(function(result) {
                if (result.success) {
                    self._render_preview(result);
                }
            });
        },

        _render_preview(data) {
            const title_el = this.$el.find('.serp-title');
            const url_el = this.$el.find('.serp-url');
            const desc_el = this.$el.find('.serp-description');

            title_el.text(data.title || 'Untitled');
            url_el.text(data.url || 'example.com');
            desc_el.text((data.description || '').substring(0, 160) + '...');
        },

        batch_generate(action, product_ids) {
            const self = this;

            return this._rpc({
                route: '/seo-ai/batch-generate',
                params: {
                    product_ids,
                    action,
                },
            }).then(function(result) {
                if (result.success) {
                    self.do_notify(_t('Success'), result.message);
                } else {
                    self.do_warn(_t('Error'), result.error);
                }
            });
        },
    });

    return {
        SEOPreview,
    };
});
