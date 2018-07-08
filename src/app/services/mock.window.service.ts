import { WindowService } from './window.service';
import { Injectable } from '@angular/core';

@Injectable()
export class MockWindowService extends WindowService {

  loadJS(url, implementationCode, location, env) {
    console.log('LoadJS mocked..');
  }
}
