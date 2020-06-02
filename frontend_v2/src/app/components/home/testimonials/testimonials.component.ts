import { Component, OnInit, Inject } from '@angular/core';
import { DOCUMENT } from '@angular/common';

/**
 * Component Class
 */
@Component({
  selector: 'app-testimonials',
  templateUrl: './testimonials.component.html',
  styleUrls: ['./testimonials.component.scss']
})
export class TestimonialsComponent implements OnInit {

  /**
   * Selected testimonial index
   */
  selected = 0;

  /**
   * Placeholder text Lorem Ipsum
   */
  ipsum: any = 'Lorem ipsum dolor sit amet,\
  consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.';

  /**
   * Sample testimonials till the API comes up
   */
  testimonials = [
    {'text': '1-' + this.ipsum, 'author': 'Lorem'},
    {'text': '2-' + this.ipsum, 'author': 'Octopus'},
    {'text': '3-' + this.ipsum, 'author': 'Penguin'}];

  /**
   * Selected testimonial text
   */
  testimonialbody = this.testimonials[this.selected]['text'];

  /**
   * Selected testimonial author
   */
  testimonialauthor = this.testimonials[this.selected]['author'];

  /**
   * Component constructor
   * @param document  Window document Injection.
   */
  constructor(@Inject(DOCUMENT) private document: Document) { }

  /**
   * Component on initialized
   */
  ngOnInit() {
  }

  /**
   * Right arrow clicked
   */
  testimonialRight() {
    this.selected = this.selected + 1;
    if (this.selected >= this.testimonials.length) {
      this.selected = 0;
    }
  }

  /**
   * left arrow clicked
   */
  testimonialLeft() {
    this.selected = this.selected - 1;
    if (this.selected < 0) {
      this.selected = this.testimonials.length - 1;
    }
  }

  /**
   * Testimonials navigated
   */
  testimonialNavigate(direction = 'left') {
    const a = this.document.getElementsByClassName('testimonial-body')[0];
    const b = this.document.getElementsByClassName('testimonial-author')[0];
    const c = this.document.getElementsByClassName('testimonial-quotes')[0];
    if (direction === 'left') {
      this.testimonialLeft();
    } else {
      this.testimonialRight();
    }
    this.flyOut(a, direction, this);
    this.disappearAppear(a, this);
    this.disappearAppear(b, this);
    this.disappearAppear(c, this);
  }

  // Testimonial animation BEGIN ----------------------------------

  /**
   * Fly left animation
   */
  flyLeftRecursive = (element, temp) => {
    const x = temp - 1;
    if (x > - 100) {
      (function(scope) {
        setTimeout(function() {
          element.style.marginLeft = x + '%';
          scope.flyLeftRecursive(element, x);
        }, 5);
      })(this);
    }
  }

  /**
   * Fly right animation
   */
  flyRightRecursive = (element, temp) => {
    const x = temp + 1;
    if (x < 100) {
      (function(scope) {
        setTimeout(function() {
          element.style.marginLeft = x + '%';
          scope.flyRightRecursive(element, x);
        }, 5);
      })(this);
    }
  }

  /**
   * Fly out animation
   */
  flyOut = (element, direction, scope) => {
    const temp = 15;
    /*
    if (direction === 'right') {
    this.flyLeftRecursive(element, temp);
    } else {
    this.flyRightRecursive(element, temp);
    }
    */
    setTimeout(function() {
      scope.testimonialbody = scope.testimonials[scope.selected]['text'];
      scope.testimonialauthor = scope.testimonials[scope.selected]['author'];
      element.style.marginLeft = '15%';
    }, 1000);
  }

  /**
   * Disappear animation
   */
  disappearAppearRecursive = (element, temp) => {
    const x = temp - 0.01;
    if (x >= 0) {
      (function(scope) {
        setTimeout(function() {
          element.style.opacity = x + '';
          scope.disappearAppearRecursive(element, x);
        }, 5);
      })(this);
    }
  }

  /**
   * Disappear animation wrapper
   */
  disappearAppear = (element, scope) => {
    const temp = 1.0;
    this.disappearAppearRecursive(element, temp);
    setTimeout(function() {
      element.style.opacity = '1';
    }, 1000);
  }

  // Testimonial animation END ----------------------------------
}
