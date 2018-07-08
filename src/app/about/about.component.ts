import { Component, OnInit, Inject } from '@angular/core';
import { GlobalService } from '../global.service';

@Component({
  selector: 'app-about',
  templateUrl: './about.component.html',
  styleUrls: ['./about.component.scss']
})
export class AboutComponent implements OnInit {

  constructor(private globalService: GlobalService) { }

  ngOnInit() {
    this.globalService.scrollToTop();
  }

}
