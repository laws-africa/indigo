import DocumentTOCView from './DocumentTOCView.vue';
import LinterPopup from './LinterPopup.vue';
import TaxonomyTOC from './TaxonomyTOC.vue';
import WorkChooser from './work_chooser';
import WorkListCard from './work_list_card';
import { VSplitter, HSplitter } from './splitters';
import { FacetGroup, RemoveFacetButton } from './facets';

export const vueComponents = {
  DocumentTOCView,
  LinterPopup,
  TaxonomyTOC
};

export const components = {
  WorkChooser,
  WorkListCard,
  FacetGroup,
  RemoveFacetButton,
  HSplitter,
  VSplitter
};
