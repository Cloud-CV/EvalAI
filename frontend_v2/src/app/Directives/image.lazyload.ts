import { AfterViewInit, Directive, ElementRef, HostBinding, Input } from '@angular/core';

@Directive({
  selector: 'img[appLazyLoadImage]'
})

export class LazyImageDirective implements AfterViewInit {

  @HostBinding('attr.src') srcAttribute = null;

  @Input() src: string;

  constructor(private el: ElementRef) {}

  ngAfterViewInit() {
    if(window && 'IntersectionObserver' in window) {
      const obs = new IntersectionObserver(entries => {
        entries.forEach(({ isIntersecting }) => {
          if (isIntersecting) {
            this.srcAttribute = this.src;
            obs.unobserve(this.el.nativeElement);
          }
        });
      });
      obs.observe(this.el.nativeElement);
    }
    else {
      this.srcAttribute = this.src;
    }
  }
}
