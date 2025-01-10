import { IEnrichment, IPopupEnrichmentProvider, PopupEnrichmentManager } from '@lawsafrica/indigo-akn/dist/enrichments/popups';
import { IRangeTarget } from '@lawsafrica/indigo-akn/dist/ranges';
import { Instance as Tippy } from 'tippy.js';
// @ts-ignore
import { createComponent } from '../vue';

class LinterEnrichment implements IEnrichment {
  public issue: any;
  public target: IRangeTarget;

  constructor (issue: any, target: IRangeTarget) {
    this.issue = issue;
    this.target = target;
  }
}

/**
 * Converts linter issues that have range targets (ie. are related to snippets of text) into popup enrichments.
 */
export class PopupIssuesProvider implements IPopupEnrichmentProvider {
  protected issues: any;
  protected vue: any;
  protected popupManager: PopupEnrichmentManager;

  constructor (issues: any, popupManager: PopupEnrichmentManager) {
    this.issues = issues;
    this.popupManager = popupManager;
    this.vue = createComponent('LinterPopup', {propsData: {issue: null}});
    this.vue.$on('fix', (issue: any) => issue.fix());
    this.vue.$mount();

    // a new issue may be added asynchronously, in which case we need to re-apply our enrichments
    // @ts-ignore
    const reapply = _.debounce(() => this.popupManager.applyProviderEnrichments(this), 200);
    this.issues.on('add', reapply);
  }

  getEnrichments(): IEnrichment[] {
    // convert issues into enrichments
    return this.issues.filter((x: any) => x.get('target')).map((issue: any) => {
      return new LinterEnrichment(issue, issue.get('target'));
    });
  }

  getPopupContent(enrichment: IEnrichment, mark: Element): Element {
    this.vue.issue = (enrichment as LinterEnrichment).issue.attributes;
    return this.vue.$el;
  }

  markCreated(enrichment: IEnrichment, mark: Element): void {
    const issue = (enrichment as LinterEnrichment).issue;
    mark.classList.add(`enrichment--${issue.attributes.severity}`);
  }

  popupCreated(enrichment: IEnrichment, popup: Tippy): void {
  }
}
