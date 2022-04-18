import { IEnrichment, IPopupEnrichmentProvider } from '@laws-africa/indigo-akn/src/enrichments/popups';
import { Instance as Tippy } from 'tippy.js';
// @ts-ignore
import { createComponent } from '../vue';

class LinterEnrichment implements IEnrichment {
  public issue: any;
  public target: object;

  constructor (issue: any, target: any) {
    this.issue = issue;
    this.target = target;
  }
}

export class PopupIssuesProvider implements IPopupEnrichmentProvider {
  protected issues: any;
  protected vue: any;

  constructor (issues: any) {
    this.issues = issues;
    this.vue = createComponent('LinterPopup', {propsData: {issue: null}});
    this.vue.$mount();
  }

  getEnrichments(): IEnrichment[] {
    // convert issues into enrichments
    return this.issues.filter((x: any) => x.get('target')).map((issue: any) => {
      return new LinterEnrichment(issue, issue.get('target'));
    });
  }

  getPopupContent(enrichment: IEnrichment, mark: Element): Element {
    const issue = enrichment as LinterEnrichment;
    this.vue.issue = issue.issue.attributes;
    return this.vue.$el;
  }

  markCreated(enrichment: IEnrichment, mark: Element): void {
    mark.classList.add('enrichment--warning');
  }

  popupCreated(enrichment: IEnrichment, popup: Tippy): void {
  }
}
