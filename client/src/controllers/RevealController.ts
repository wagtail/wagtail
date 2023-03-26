import { Controller } from '@hotwired/stimulus';

/**
 *
 * @example
 * <section
 * data-controller="w-panel"
 * data-action="w-panel:toggle->w-panel#toggle"
 * >
 *   <div>
 *       <a w-panel-target="anchor">
 *       </a>
 *       <button data-action="w-panel->toggle">
 *       </button>
 *           <h2 w-panel-target="heading">
 *                   <span w-panel-target="heading-text"></span>
 *           </h2>
 *           <div w-panel-target="controls">
 *           </div>
 *   </div>
 *   <div
 * w-panel-target="item"
 * data-action="beforematch->w-panel#toggle"
 * >
 *   </div>
 * </section>
 * */
export class RevealController extends Controller<HTMLButtonElement> {
    declare readonly hasHiddenClass: boolean
    declare readonly hiddenClass: string
    declare readonly itemTargets: HTMLElement[]
    declare class: string
  
    static targets = ['item']
    static classes = ['hidden']
  
    connect (): void {
      this.class = this.hasHiddenClass ? this.hiddenClass : 'hidden'
    }
  
    toggle (): void {
      this.itemTargets.forEach(item => {
        item.classList.toggle(this.class)
      })
    }
  
    show (): void {
      this.itemTargets.forEach(item => {
        item.classList.remove(this.class)
      })
    }
  
    hide (): void {
      this.itemTargets.forEach(item => {
        item.classList.add(this.class)
      })
    }
}
