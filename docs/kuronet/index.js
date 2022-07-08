/*
 * IIIF Curation Viewer v1.8
 * http://codh.rois.ac.jp/software/iiif-curation-viewer/
 *
 * Copyright 2016 Center for Open Data in the Humanities, Research Organization of Information and Systems
 * Released under the MIT license
 *
 * Core contributor: Jun HOMMA (@2SC1815J)
 *
 * Licenses of open source libraries, see acknowledgements.txt
 */
var iiifViewer = (function() {
    var configExample = {
        title: [
            {
                '@language': 'en',
                '@value': '<span class="icp_navbar_brand_logo"></span>KuroNet Text Editor'
            },
            {
                '@language': 'ja',
                '@value': '<span class="icp_navbar_brand_logo"></span>KuroNet Text Editor'
            }
        ],
        trustedUrlPrefixes: ['https://', 'http://'], //無制限
        service: {
            curationJsonExportUrl: 'https://mp.ex.nii.ac.jp/api/curation/json'
        }
    };
    return IIIFCurationViewer(configExample);
})();
