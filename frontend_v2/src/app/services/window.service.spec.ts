import { TestBed, inject } from '@angular/core/testing';

import { WindowService } from './window.service';

describe('WindowService', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [WindowService],
    });
  });

  /**
   * Download File function test.
   */
  it('should be created', inject([WindowService], (service: WindowService) => {
    expect(service).toBeTruthy();
    const NW = service.nativeWindow();
  }));

  /**
   * Download File function test.
   */
  it('Download File Test', inject([WindowService], (service: WindowService) => {
    expect(service).toBeTruthy();
    const SELF = this;
    SELF.test = () => {};
    const SPY = spyOn(SELF, 'test');
    service.downloadFile('', 'data_test.csv', { type: 'text/csv' }, SPY);
    expect(SPY).toHaveBeenCalled();
  }));

  /**
   * loadJS function test.
   */
  it('script file should be loaded', inject([WindowService], (service: WindowService) => {
    expect(service).toBeTruthy();
    const SELF = this;
    SELF.appendChild = () => {};
    const SPY = spyOn(SELF, 'appendChild');
    service.loadJS('', (env) => {}, SELF, null);
    expect(SPY).toHaveBeenCalled();
  }));
});
