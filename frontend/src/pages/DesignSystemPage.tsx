import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Field, Input } from "../components/ui/Input";
import { ScoreBar } from "../components/ui/ScoreBar";

export function DesignSystemPage() {
  return (
    <div className="space-y-8 max-w-3xl">
      <div>
        <h1 className="text-display">Research desk design system</h1>
        <p className="mt-2 text-[var(--color-text-secondary)]">Warm paper, ink type, plum accents. Scores use ink and plum — never red-to-green.</p>
      </div>
      <section className="space-y-3">
        <h2 className="text-subheading">Typography</h2>
        <p className="text-title">Newsreader title</p>
        <p className="text-body">IBM Plex Sans body at 14/22.</p>
        <p className="font-mono font-tabular text-label">REQ-10482 · 82</p>
      </section>
      <section className="space-y-3">
        <h2 className="text-subheading">Buttons</h2>
        <div className="flex flex-wrap gap-2">
          <Button>Primary action</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="quiet">Quiet</Button>
        </div>
      </section>
      <section className="space-y-3">
        <h2 className="text-subheading">Badges and score</h2>
        <div className="flex flex-wrap gap-2">
          <Badge tone="ochre">New since yesterday</Badge>
          <Badge tone="success">Met requirement</Badge>
          <Badge tone="warning">Closing soon</Badge>
        </div>
        <ScoreBar score={82} />
      </section>
      <section className="space-y-3">
        <h2 className="text-subheading">Form</h2>
        <Field label="Role search" help="Opened with / on Discover.">
          <Input name="demo" />
        </Field>
      </section>
    </div>
  );
}
