import { Component, OnInit } from '@angular/core';
import {GlobalService} from '../../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-loading',
  templateUrl: './loading.component.html',
  styleUrls: ['./loading.component.scss']
})
export class LoadingComponent implements OnInit {

  /**
   * Constructor.
   */
  constructor(public globalService: GlobalService) { }

  /**
   * Component on intialized
   */
  ngOnInit() {
  }

}
