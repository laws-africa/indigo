import { IEnrichment, IEnrichmentProvider } from '@laws-africa/indigo-akn/src/enrichments/popups';
import { Instance as Tippy } from 'tippy.js';

class LinterEnrichment implements IEnrichment {
  public issue: any;
  public target: object;

  constructor (issue: any, target: any) {
    this.issue = issue;
    this.target = target;
  }
}

export class PopupIssuesProvider implements IEnrichmentProvider {
  private issues: any;

  constructor (issues: any) {
    this.issues = issues;
  }

  getEnrichments(): IEnrichment[] {
    return [new LinterEnrichment({
      message: 'hi',
    }, {
      anchor_id: 'sec_1_2__p_1',
      selectors: [{
        type: 'TextPositionSelector',
        start: 0,
        end: 4,
      }]
    })];

    // convert issues into enrichments
    return this.issues.map((issue: any) => {
      return new LinterEnrichment(issue, {
        anchor_id: 'sec_1_2__p_1',
        selectors: [{
          type: 'TextPositionSelector',
          start: 0,
          end: 4,
        }]
      });
    });
  }

  getPopupContent(enrichment: IEnrichment, mark: Element): Element {
    const issue = enrichment as LinterEnrichment;
    const div = window.document.createElement('div');
    div.innerText = issue.issue.message;
    return div;
  }

  markCreated(enrichment: IEnrichment, mark: Element): void {
    mark.classList.add('enrichment--warning');
  }

  markDestroyed(enrichment: IEnrichment, mark: Element): void {
  }

  popupCreated(popup: Tippy): void {
  }
}
