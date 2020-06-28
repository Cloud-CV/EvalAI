import { Component, OnInit } from '@angular/core';

/**
 * Component Class
 */
@Component({
  selector: 'app-rules',
  templateUrl: './rules.component.html',
  styleUrls: ['./rules.component.scss']
})
export class RulesComponent implements OnInit {
  /**
   * Placeholder text Lorem Ipsum
   */
  ipsum: any = 'Lorem ipsum dolor sit amet,\
  consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.';

  /**
   * Component Constructor
   */
  constructor() { }

  /**
   * Component on initialized
   */
  ngOnInit() {
  }

}
