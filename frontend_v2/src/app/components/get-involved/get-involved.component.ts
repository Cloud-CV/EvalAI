import { Component, OnInit } from '@angular/core';
import { GlobalService } from '../../services/global.service';

/**
 * Component Class
 */
@Component({
  selector: 'app-get-involved',
  templateUrl: './get-involved.component.html',
  styleUrls: ['./get-involved.component.scss'],
})
export class GetInvolvedComponent implements OnInit {
  /**
   * Constructor.
   * @param globalService  GlobalService Injection.
   */
  constructor(public globalService: GlobalService) {}

  /**
   * Component on initialized.
   */
  ngOnInit() {
    this.globalService.scrollToTop();
  }
}
