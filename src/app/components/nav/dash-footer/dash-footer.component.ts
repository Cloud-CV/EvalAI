import {Component, Inject, OnInit} from '@angular/core';
import {DOCUMENT} from '@angular/common';

@Component({
  selector: 'app-dash-footer',
  templateUrl: './dash-footer.component.html',
  styleUrls: ['./dash-footer.component.scss']
})
export class DashFooterComponent implements OnInit {

  year: any;

  constructor(@Inject(DOCUMENT) private document: Document) { }

  ngOnInit() {
    this.year = new Date().getFullYear();
  }

}
