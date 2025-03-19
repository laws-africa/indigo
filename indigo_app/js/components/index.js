import DocumentTOCView from './DocumentTOCView.vue';
import LinterPopup from './LinterPopup.vue';
import TaxonomyTOC from './TaxonomyTOC.vue';
import WorkChooser from './work_chooser';
import ListCard from './list_card';
import { VSplitter, HSplitter } from './splitters';
import { FacetGroup, RemoveFacetButton } from './facets';

export const vueComponents = {
  DocumentTOCView,
  LinterPopup,
  TaxonomyTOC
};

export const components = {
  WorkChooser,
  ListCard,
  FacetGroup,
  RemoveFacetButton,
  HSplitter,
  VSplitter
};
