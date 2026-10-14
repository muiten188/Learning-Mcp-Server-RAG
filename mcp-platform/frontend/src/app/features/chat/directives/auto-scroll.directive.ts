import { Directive, ElementRef, inject, Input, OnChanges } from '@angular/core';

@Directive({ selector: '[appAutoScroll]', standalone: true })
export class AutoScrollDirective implements OnChanges {
  private readonly element = inject(ElementRef<HTMLElement>);
  @Input() appAutoScroll: unknown;
  ngOnChanges() {
    queueMicrotask(() => {
      const element = this.element.nativeElement;
      element.scrollTop = element.scrollHeight;
    });
  }
}
